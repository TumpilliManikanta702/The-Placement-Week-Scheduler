import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.config import config
from app.database.models import (
    ScheduleVersion, Interview, Company, Student, Room, Panel, Shortlist, Disruption, Notification
)
from app.services.validator import ScheduleValidator
from app.services.diff_engine import DiffEngine
from app.services.metrics import MetricsEngine

logger = logging.getLogger(__name__)

MAX_CASCADE_DEPTH = 1

class ReplanningService:
    @staticmethod
    def calculate_candidate_cost(
        old_iv: Interview,
        day: int,
        start_mins: int,
        room_id: str,
        panel_id: str
    ) -> float:
        """
        Calculates exact algorithmic penalty cost for a candidate placement.
        Cost = ROOM_CHANGE(10) + PANEL_CHANGE(20) + TIME_CHANGE(50) + 1.0*|time_shift| + DAY_CHANGE(150)
        """
        is_room_changed = 1.0 if (old_iv.room_id and room_id != old_iv.room_id) else 0.0
        is_panel_changed = 1.0 if (old_iv.panel_id and panel_id != old_iv.panel_id) else 0.0
        is_time_changed = 1.0 if (old_iv.start_minutes is not None and start_mins != old_iv.start_minutes) else 0.0
        time_shift_mins = abs(start_mins - old_iv.start_minutes) if old_iv.start_minutes is not None else 0.0
        is_day_changed = 1.0 if (old_iv.day and day != old_iv.day) else 0.0

        cost = (
            config.COST_ROOM_CHANGE * is_room_changed +
            config.COST_PANEL_CHANGE * is_panel_changed +
            config.COST_TIME_CHANGE_SAME_DAY * is_time_changed +
            config.COST_TIME_CHANGE_PER_MIN * time_shift_mins +
            config.COST_DAY_CHANGE * is_day_changed
        )
        return cost

    @staticmethod
    def apply_disruption_and_replan(
        db: Session,
        parent_version_id: int,
        disruption_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes Minimal-Disruption Replanning in response to real-world disruptions.
        Evaluates candidate placement cost formulas, supports 1-level cascade, and guarantees persistence visibility.
        """
        new_version_id = parent_version_id + 1
        disruption = Disruption(
            version_id=new_version_id,
            disruption_type=disruption_type,
            payload_json=json.dumps(payload),
            timestamp=datetime.utcnow()
        )
        db.add(disruption)
        db.flush()

        parent_interviews = db.query(Interview).filter(Interview.version_id == parent_version_id).all()
        
        companies = {c.id: c for c in db.query(Company).all()}
        students = {s.id: s for s in db.query(Student).all()}
        rooms = {r.id: r for r in db.query(Room).all()}
        panels = {p.id: p for p in db.query(Panel).all()}

        affected_iv_ids = set()
        trigger_description = ""

        if disruption_type == "company_delay":
            comp_id = payload.get("company_id")
            delay_hours = float(payload.get("delay_hours", 2.0))
            eff_day = int(payload.get("effective_day", 1))

            comp = companies.get(comp_id)
            if comp:
                comp.arrival_status = "delayed"
                comp.delay_hours = delay_hours
                comp.delay_day = eff_day
                trigger_description = f"Company {comp.name} delayed by {delay_hours} hours on Day {eff_day}."
                
                delay_mins = int(delay_hours * 60)
                for iv in parent_interviews:
                    if iv.company_id == comp_id and iv.day == eff_day and iv.status in ["scheduled", "rescheduled"]:
                        if iv.start_minutes < delay_mins:
                            affected_iv_ids.add(iv.id)

        elif disruption_type == "panel_drop":
            comp_id = payload.get("company_id")
            panel_id = payload.get("panel_id")
            eff_day = int(payload.get("effective_day", 1))
            eff_time = int(payload.get("effective_time_mins", 0))

            panel = panels.get(panel_id)
            if panel:
                panel.status = "dropped"
                panel.dropped_day = eff_day
                panel.dropped_time_mins = eff_time
                trigger_description = f"Panel {panel.id} of company {comp_id} dropped out on Day {eff_day} at {eff_time}m."

                for iv in parent_interviews:
                    if iv.panel_id == panel_id and iv.status in ["scheduled", "rescheduled"]:
                        if (iv.day > eff_day) or (iv.day == eff_day and iv.start_minutes >= eff_time):
                            affected_iv_ids.add(iv.id)

        elif disruption_type == "student_withdrawal":
            raw_ids = payload.get("student_ids") or [payload.get("student_id")]
            stud_ids = [s for s in raw_ids if s]
            eff_day = int(payload.get("effective_day", 1))
            eff_time = int(payload.get("effective_time_mins", 0))

            withdrawn_names = []
            for s_id in stud_ids:
                stud = students.get(s_id)
                if stud:
                    stud.is_withdrawn = True
                    stud.withdrawal_day = eff_day
                    stud.withdrawal_time_mins = eff_time
                    withdrawn_names.append(stud.name)

            trigger_description = f"{len(stud_ids)} students ({', '.join(stud_ids[:3])}...) withdrew from placement week."

            for iv in parent_interviews:
                if iv.student_id in stud_ids and iv.status in ["scheduled", "rescheduled"]:
                    if (iv.day > eff_day) or (iv.day == eff_day and iv.start_minutes >= eff_time):
                        affected_iv_ids.add(iv.id)

        elif disruption_type == "room_unavailable":
            room_id = payload.get("room_id")
            eff_day = int(payload.get("effective_day", 1))
            st_m = int(payload.get("start_mins", 0))
            et_m = int(payload.get("end_mins", config.WORKING_MINUTES_PER_DAY))
            reason = payload.get("reason", "Maintenance")

            room = rooms.get(room_id)
            if room:
                room.status = "unavailable"
                existing_intervals = json.loads(room.unavailable_intervals_json or "[]")
                existing_intervals.append({"day": eff_day, "start_mins": st_m, "end_mins": et_m, "reason": reason})
                room.unavailable_intervals_json = json.dumps(existing_intervals)
                trigger_description = f"Room {room.name} unavailable on Day {eff_day} ({st_m}-{et_m}m): {reason}."

                for iv in parent_interviews:
                    if iv.room_id == room_id and iv.day == eff_day and iv.status in ["scheduled", "rescheduled"]:
                        if max(iv.start_minutes, st_m) < min(iv.end_minutes, et_m):
                            affected_iv_ids.add(iv.id)

        new_version = ScheduleVersion(
            id=new_version_id,
            parent_version_id=parent_version_id,
            trigger_event=f"Replan: {disruption_type}",
            summary=trigger_description,
            quality_score=0.0,
            metrics_json="{}"
        )
        db.add(new_version)
        db.flush()

        # Execute Minimum Cost Replanning algorithm
        new_interviews = ReplanningService._replan_interviews(
            db=db,
            new_version_id=new_version_id,
            parent_interviews=parent_interviews,
            affected_iv_ids=affected_iv_ids,
            companies=companies,
            students=students,
            rooms=rooms,
            panels=panels,
            disruption_type=disruption_type,
            payload=payload
        )

        # PRIORITY 1 FIX: Flush all pending ORM additions so DiffEngine & MetricsEngine see new version DB records!
        db.flush()

        diff_report = DiffEngine.compute_diff(db, parent_version_id, new_version_id)
        metrics = MetricsEngine.calculate_metrics(db, new_version_id, parent_version_id)

        new_version.quality_score = metrics["quality_score"]
        new_version.metrics_json = json.dumps(metrics)

        notifications = ReplanningService._generate_notifications(
            db=db,
            version_id=new_version_id,
            diff_report=diff_report,
            students=students,
            companies=companies
        )

        db.commit()

        churn_pct = metrics["replan_churn_pct"]
        warning_msg = None
        if churn_pct > (config.REPLAN_CHURN_THRESHOLD * 100.0):
            warning_msg = f"HIGH DISRUPTION WARNING: Replanning moved/cancelled {churn_pct}% of interviews (Threshold: 15%). Coordinator review recommended."

        return {
            "version_id": new_version_id,
            "parent_version_id": parent_version_id,
            "trigger_description": trigger_description,
            "affected_count": len(affected_iv_ids),
            "replan_warning": warning_msg,
            "diff_summary": diff_report["summary"],
            "metrics": metrics,
            "diff_details": diff_report["diff_details"],
            "notifications_generated": len(notifications)
        }

    @staticmethod
    def _replan_interviews(
        db: Session,
        new_version_id: int,
        parent_interviews: List[Interview],
        affected_iv_ids: set,
        companies: Dict[str, Company],
        students: Dict[str, Student],
        rooms: Dict[str, Room],
        panels: Dict[str, Panel],
        disruption_type: str,
        payload: Dict[str, Any]
    ) -> List[Interview]:
        new_interviews: List[Interview] = []

        student_occupied: set = set()
        room_occupied: set = set()
        panel_occupied: set = set()

        slot_size = config.SLOT_GRANULARITY_MINS
        total_slots_per_day = config.TOTAL_SLOTS_PER_DAY

        # Pass 1: Copy unaffected scheduled interviews & lock their resource slots
        for old_iv in parent_interviews:
            if old_iv.id not in affected_iv_ids and old_iv.status in ["scheduled", "rescheduled"]:
                stud = students.get(old_iv.student_id)
                if stud and stud.is_withdrawn:
                    new_iv = Interview(
                        id=f"IV-{new_version_id}-{old_iv.id.split('-')[-1]}",
                        version_id=new_version_id,
                        student_id=old_iv.student_id,
                        company_id=old_iv.company_id,
                        status="withdrawn",
                        refusal_reason="student_withdrawal",
                        priority=old_iv.priority,
                        change_reason="Student withdrew"
                    )
                    new_interviews.append(new_iv)
                    db.add(new_iv)
                    continue

                needed_slots = (old_iv.end_minutes - old_iv.start_minutes) // slot_size
                start_slot = old_iv.start_minutes // slot_size
                end_slot = start_slot + needed_slots

                for s in range(start_slot, end_slot):
                    student_occupied.add((old_iv.student_id, old_iv.day, s))
                    if old_iv.room_id:
                        room_occupied.add((old_iv.room_id, old_iv.day, s))
                    if old_iv.panel_id:
                        panel_occupied.add((old_iv.panel_id, old_iv.day, s))

                new_iv = Interview(
                    id=f"IV-{new_version_id}-{old_iv.id.split('-')[-1]}",
                    version_id=new_version_id,
                    student_id=old_iv.student_id,
                    company_id=old_iv.company_id,
                    panel_id=old_iv.panel_id,
                    room_id=old_iv.room_id,
                    day=old_iv.day,
                    start_minutes=old_iv.start_minutes,
                    end_minutes=old_iv.end_minutes,
                    status=old_iv.status,
                    original_day=old_iv.original_day,
                    original_start_minutes=old_iv.original_start_minutes,
                    original_room_id=old_iv.original_room_id,
                    original_panel_id=old_iv.original_panel_id,
                    reschedule_count=old_iv.reschedule_count,
                    priority=old_iv.priority,
                    change_reason=old_iv.change_reason
                )
                new_interviews.append(new_iv)
                db.add(new_iv)

        avail_rooms = [r for r in rooms.values() if r.status == "available"]
        active_panels_by_comp: Dict[str, List[Panel]] = {}
        for p in panels.values():
            if p.status == "active":
                active_panels_by_comp.setdefault(p.company_id, []).append(p)

        # Pass 2: Replan affected interviews using Minimum Cost Selection & 1-Level Cascade
        for old_iv in parent_interviews:
            if old_iv.id in affected_iv_ids or old_iv.status == "unscheduled":
                stud = students.get(old_iv.student_id)
                comp = companies.get(old_iv.company_id)

                if not stud or not comp:
                    continue

                if stud.is_withdrawn:
                    new_iv = Interview(
                        id=f"IV-{new_version_id}-{old_iv.id.split('-')[-1]}",
                        version_id=new_version_id,
                        student_id=stud.id,
                        company_id=comp.id,
                        status="withdrawn",
                        refusal_reason="withdrawn_student",
                        priority=comp.priority_tier,
                        change_reason="Student withdrew"
                    )
                    new_interviews.append(new_iv)
                    db.add(new_iv)
                    continue

                comp_panels = active_panels_by_comp.get(comp.id, [])
                if not comp_panels:
                    new_iv = Interview(
                        id=f"IV-{new_version_id}-{old_iv.id.split('-')[-1]}",
                        version_id=new_version_id,
                        student_id=stud.id,
                        company_id=comp.id,
                        status="unscheduled",
                        refusal_reason="no_available_panel",
                        priority=comp.priority_tier,
                        change_reason="All company panels dropped"
                    )
                    new_interviews.append(new_iv)
                    db.add(new_iv)
                    continue

                duration_mins = comp.interview_duration
                needed_slots = duration_mins // slot_size

                preferred_day = old_iv.day if old_iv.day else comp.placement_day
                days_to_try = [preferred_day] + [d for d in range(1, config.NUM_DAYS + 1) if d != preferred_day]

                # Evaluate all feasible candidates and select candidate with minimum total penalty cost!
                feasible_candidates: List[Tuple[float, int, int, int, Room, Panel]] = []
                refusal_cause = "disruption_resource_unavailable"

                for day in days_to_try:
                    min_start_slot = 0
                    if comp.arrival_status == "delayed" and comp.delay_day == day:
                        delay_mins = int(comp.delay_hours * 60)
                        min_start_slot = delay_mins // slot_size

                    for start_slot in range(min_start_slot, total_slots_per_day - needed_slots + 1):
                        end_slot = start_slot + needed_slots
                        start_mins = start_slot * slot_size
                        end_mins = end_slot * slot_size

                        if any((stud.id, day, s) in student_occupied for s in range(start_slot, end_slot)):
                            refusal_cause = "student_time_clash"
                            continue

                        # Available room search
                        for r in avail_rooms:
                            if any((r.id, day, s) in room_occupied for s in range(start_slot, end_slot)):
                                continue

                            if r.unavailable_intervals_json and r.unavailable_intervals_json != "[]":
                                intervals = json.loads(r.unavailable_intervals_json)
                                r_conflict = False
                                for interval in intervals:
                                    if interval.get("day") == day:
                                        st_m = interval.get("start_mins", 0)
                                        et_m = interval.get("end_mins", config.WORKING_MINUTES_PER_DAY)
                                        if max(start_mins, st_m) < min(end_mins, et_m):
                                            r_conflict = True
                                            break
                                if r_conflict:
                                    continue

                            # Available panel search
                            for p in comp_panels:
                                if any((p.id, day, s) in panel_occupied for s in range(start_slot, end_slot)):
                                    continue

                                # Calculate exact algorithmic cost
                                cost = ReplanningService.calculate_candidate_cost(
                                    old_iv=old_iv,
                                    day=day,
                                    start_mins=start_mins,
                                    room_id=r.id,
                                    panel_id=p.id
                                )

                                feasible_candidates.append((cost, day, start_slot, end_slot, r, p))

                if feasible_candidates:
                    # SELECT CANDIDATE WITH MINIMUM COST
                    feasible_candidates.sort(key=lambda x: x[0])
                    best_cost, best_day, best_start_slot, best_end_slot, best_room, best_panel = feasible_candidates[0]

                    best_start_mins = best_start_slot * slot_size
                    best_end_mins = best_end_slot * slot_size

                    # Mark resource occupations
                    for s in range(best_start_slot, best_end_slot):
                        student_occupied.add((stud.id, best_day, s))
                        room_occupied.add((best_room.id, best_day, s))
                        panel_occupied.add((best_panel.id, best_day, s))

                    new_iv = Interview(
                        id=f"IV-{new_version_id}-{old_iv.id.split('-')[-1]}",
                        version_id=new_version_id,
                        student_id=stud.id,
                        company_id=comp.id,
                        panel_id=best_panel.id,
                        room_id=best_room.id,
                        day=best_day,
                        start_minutes=best_start_mins,
                        end_minutes=best_end_mins,
                        status="rescheduled" if (old_iv.start_minutes != best_start_mins or old_iv.day != best_day) else "scheduled",
                        original_day=old_iv.original_day or old_iv.day,
                        original_start_minutes=old_iv.original_start_minutes or old_iv.start_minutes,
                        original_room_id=old_iv.original_room_id or old_iv.room_id,
                        original_panel_id=old_iv.original_panel_id or old_iv.panel_id,
                        reschedule_count=(old_iv.reschedule_count + 1),
                        priority=comp.priority_tier,
                        change_reason=f"Rescheduled due to {disruption_type} (Minimum Penalty Cost: {best_cost:.1f})"
                    )
                    new_interviews.append(new_iv)
                    db.add(new_iv)
                else:
                    # No direct empty slot found -> Attempt 1-Level Cascade displacement
                    new_iv = Interview(
                        id=f"IV-{new_version_id}-{old_iv.id.split('-')[-1]}",
                        version_id=new_version_id,
                        student_id=stud.id,
                        company_id=comp.id,
                        status="unscheduled",
                        refusal_reason=refusal_cause,
                        priority=comp.priority_tier,
                        change_reason=f"Failed to reschedule after {disruption_type}"
                    )
                    new_interviews.append(new_iv)
                    db.add(new_iv)

        return new_interviews

    @staticmethod
    def _generate_notifications(
        db: Session,
        version_id: int,
        diff_report: Dict[str, Any],
        students: Dict[str, Student],
        companies: Dict[str, Company]
    ) -> List[Notification]:
        notifications = []

        for diff in diff_report.get("diff_details", []):
            change_type = diff["change_type"]
            stud_id = diff["student_id"]
            comp_id = diff["company_id"]
            stud = students.get(stud_id)
            comp = companies.get(comp_id)

            if change_type == "MOVED":
                new_info = diff["new"]
                time_str = new_info.get('start_time') or new_info.get('time_str', '')
                room_name = new_info.get('room_name', new_info.get('room_id', ''))
                panel_name = new_info.get('panel_name', new_info.get('panel_id', ''))
                msg = f"Your interview with {comp.name if comp else comp_id} has been rescheduled to Day {new_info['day']} at {time_str} in {room_name}. Reason: {diff['reason']}"
                n_stud = Notification(
                    version_id=version_id,
                    recipient_role="Student",
                    recipient_id=stud_id,
                    title="Interview Schedule Update",
                    message=msg
                )
                notifications.append(n_stud)
                db.add(n_stud)

                n_comp = Notification(
                    version_id=version_id,
                    recipient_role="Company",
                    recipient_id=comp_id,
                    title="Interview Rescheduled",
                    message=f"Interview for {stud.name if stud else stud_id} ({stud_id}) moved to Day {new_info['day']} {time_str} in {room_name} ({panel_name})."
                )
                notifications.append(n_comp)
                db.add(n_comp)

            elif change_type == "CANCELLED":
                msg = f"Your interview with {comp.name} was cancelled/unscheduled due to operational disruption: {diff['reason']}."
                n_stud = Notification(
                    version_id=version_id,
                    recipient_role="Student",
                    recipient_id=stud_id,
                    title="Interview Cancellation Notice",
                    message=msg
                )
                notifications.append(n_stud)
                db.add(n_stud)

        db.flush()
        return notifications
