import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.config import config
from app.database.models import Interview, Company, Student, Room, Panel, Shortlist, Disruption, ScheduleVersion

class ValidationReport:
    def __init__(self, is_valid: bool, violations: List[Dict[str, Any]], summary: Dict[str, int]):
        self.is_valid = is_valid
        self.violations = violations
        self.summary = summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "violations_count": len(self.violations),
            "summary": self.summary,
            "violations": self.violations
        }

class ScheduleValidator:
    @staticmethod
    def validate_version(db: Session, version_id: int) -> ValidationReport:
        interviews = db.query(Interview).filter(
            Interview.version_id == version_id,
            Interview.status.in_(["scheduled", "rescheduled"])
        ).all()

        companies = {c.id: c for c in db.query(Company).all()}
        students = {s.id: s for s in db.query(Student).all()}
        rooms = {r.id: r for r in db.query(Room).all()}
        panels = {p.id: p for p in db.query(Panel).all()}
        
        # Build shortlist lookup set: (student_id, company_id)
        shortlists = set(
            (sl.student_id, sl.company_id) 
            for sl in db.query(Shortlist).all()
        )

        # VERSION-SCOPED DISRUPTION STATE RECONSTRUCTION
        # Collect disruptions active for version_id (disruptions with version_id <= target version_id)
        active_disruptions = db.query(Disruption).filter(
            Disruption.version_id <= version_id
        ).all()

        delayed_companies: Dict[str, Dict[str, Any]] = {}
        dropped_panels: Dict[str, Dict[str, Any]] = {}
        withdrawn_students: Dict[str, Dict[str, Any]] = {}
        unavailable_rooms: Dict[str, List[Dict[str, Any]]] = {}

        for d in active_disruptions:
            try:
                payload = json.loads(d.payload_json or "{}")
            except Exception:
                payload = {}

            if d.disruption_type == "company_delay":
                c_id = payload.get("company_id")
                if c_id:
                    delayed_companies[c_id] = {
                        "delay_hours": float(payload.get("delay_hours", 2.0)),
                        "delay_day": int(payload.get("effective_day", 1))
                    }
            elif d.disruption_type == "panel_drop":
                p_id = payload.get("panel_id")
                if p_id:
                    dropped_panels[p_id] = {
                        "effective_day": int(payload.get("effective_day", 1)),
                        "effective_time_mins": int(payload.get("effective_time_mins", 0))
                    }
            elif d.disruption_type == "student_withdrawal":
                raw_ids = payload.get("student_ids") or [payload.get("student_id")]
                for s_id in raw_ids:
                    if s_id:
                        withdrawn_students[s_id] = {
                            "effective_day": int(payload.get("effective_day", 1)),
                            "effective_time_mins": int(payload.get("effective_time_mins", 0))
                        }
            elif d.disruption_type == "room_unavailable":
                r_id = payload.get("room_id")
                if r_id:
                    unavailable_rooms.setdefault(r_id, []).append({
                        "day": int(payload.get("effective_day", 1)),
                        "start_mins": int(payload.get("start_mins", 0)),
                        "end_mins": int(payload.get("end_mins", config.WORKING_MINUTES_PER_DAY))
                    })

        violations = []
        summary = {
            "student_conflicts": 0,
            "room_conflicts": 0,
            "panel_conflicts": 0,
            "working_hour_violations": 0,
            "withdrawn_student_violations": 0,
            "resource_unavailability_violations": 0,
            "invalid_assignments": 0,
            "duration_violations": 0
        }

        # Index interviews for overlap checking
        student_day_map: Dict[str, List[Interview]] = {}
        room_day_map: Dict[str, List[Interview]] = {}
        panel_day_map: Dict[str, List[Interview]] = {}

        for iv in interviews:
            # 1. Basic field validity & working hours check
            if iv.day is None or iv.start_minutes is None or iv.end_minutes is None:
                summary["invalid_assignments"] += 1
                violations.append({
                    "type": "invalid_assignment",
                    "severity": "HIGH",
                    "interview_id": iv.id,
                    "description": f"Interview {iv.id} missing schedule day/time."
                })
                continue

            comp = companies.get(iv.company_id)
            duration = iv.end_minutes - iv.start_minutes

            if comp and duration != comp.interview_duration:
                summary["duration_violations"] += 1
                violations.append({
                    "type": "duration_violation",
                    "severity": "HIGH",
                    "interview_id": iv.id,
                    "description": f"Interview duration {duration}m does not match company requirement {comp.interview_duration}m."
                })

            if iv.start_minutes < 0 or iv.end_minutes > config.WORKING_MINUTES_PER_DAY:
                summary["working_hour_violations"] += 1
                violations.append({
                    "type": "working_hour_violation",
                    "severity": "HIGH",
                    "interview_id": iv.id,
                    "description": f"Interview {iv.id} ({iv.start_minutes}-{iv.end_minutes}m) exceeds daily working hours (0-480m)."
                })

            # 2. Company Arrival Delay check (Version-Scoped)
            if iv.company_id in delayed_companies:
                d_info = delayed_companies[iv.company_id]
                delay_mins = int(d_info["delay_hours"] * 60)
                if iv.day == d_info["delay_day"] and iv.start_minutes < delay_mins:
                    summary["working_hour_violations"] += 1
                    violations.append({
                        "type": "company_delay_violation",
                        "severity": "HIGH",
                        "interview_id": iv.id,
                        "description": f"Interview scheduled at {iv.start_minutes}m, but company {iv.company_id} is delayed until {delay_mins}m on Day {d_info['delay_day']}."
                    })

            # 3. Shortlist check
            if (iv.student_id, iv.company_id) not in shortlists:
                summary["invalid_assignments"] += 1
                violations.append({
                    "type": "unshortlisted_assignment",
                    "severity": "HIGH",
                    "interview_id": iv.id,
                    "description": f"Student {iv.student_id} is not shortlisted by company {iv.company_id}."
                })

            # 4. Withdrawn student check (Version-Scoped)
            if iv.student_id in withdrawn_students:
                w_info = withdrawn_students[iv.student_id]
                w_day = w_info["effective_day"]
                w_time = w_info["effective_time_mins"]
                if (iv.day > w_day) or (iv.day == w_day and iv.start_minutes >= w_time):
                    summary["withdrawn_student_violations"] += 1
                    violations.append({
                        "type": "withdrawn_student_violation",
                        "severity": "HIGH",
                        "interview_id": iv.id,
                        "description": f"Withdrawn student {iv.student_id} assigned interview on Day {iv.day} at {iv.start_minutes}m."
                    })

            # 5. Panel-Company binding & Panel status check (Version-Scoped)
            panel = panels.get(iv.panel_id) if iv.panel_id else None
            if panel:
                if panel.company_id != iv.company_id:
                    summary["invalid_assignments"] += 1
                    violations.append({
                        "type": "panel_company_mismatch",
                        "severity": "HIGH",
                        "interview_id": iv.id,
                        "description": f"Panel {panel.id} belongs to {panel.company_id}, not {iv.company_id}."
                    })
                if iv.panel_id in dropped_panels:
                    dp_info = dropped_panels[iv.panel_id]
                    dp_day = dp_info["effective_day"]
                    dp_time = dp_info["effective_time_mins"]
                    if (iv.day > dp_day) or (iv.day == dp_day and iv.start_minutes >= dp_time):
                        summary["resource_unavailability_violations"] += 1
                        violations.append({
                            "type": "dropped_panel_violation",
                            "severity": "HIGH",
                            "interview_id": iv.id,
                            "description": f"Dropped panel {iv.panel_id} assigned interview on Day {iv.day} at {iv.start_minutes}m."
                        })

            # 6. Room availability check (Version-Scoped)
            if iv.room_id and iv.room_id in unavailable_rooms:
                for interval in unavailable_rooms[iv.room_id]:
                    if interval.get("day") == iv.day:
                        st = interval.get("start_mins", 0)
                        et = interval.get("end_mins", config.WORKING_MINUTES_PER_DAY)
                        if max(iv.start_minutes, st) < min(iv.end_minutes, et):
                            summary["resource_unavailability_violations"] += 1
                            violations.append({
                                "type": "unavailable_room_violation",
                                "severity": "HIGH",
                                "interview_id": iv.id,
                                "description": f"Room {iv.room_id} is unavailable on Day {iv.day} between {st}-{et}m."
                            })

            # Maps for overlap checks
            s_key = f"{iv.student_id}_D{iv.day}"
            student_day_map.setdefault(s_key, []).append(iv)

            if iv.room_id:
                r_key = f"{iv.room_id}_D{iv.day}"
                room_day_map.setdefault(r_key, []).append(iv)

            if iv.panel_id:
                p_key = f"{iv.panel_id}_D{iv.day}"
                panel_day_map.setdefault(p_key, []).append(iv)

        # 7. Check Overlaps (Student, Room, Panel)
        def find_overlaps(items: List[Interview], key_type: str, error_counter: str):
            items_sorted = sorted(items, key=lambda x: x.start_minutes)
            for i in range(len(items_sorted)):
                for j in range(i + 1, len(items_sorted)):
                    a, b = items_sorted[i], items_sorted[j]
                    if a.start_minutes < b.end_minutes and b.start_minutes < a.end_minutes:
                        summary[error_counter] += 1
                        violations.append({
                            "type": f"{key_type}_conflict",
                            "severity": "CRITICAL",
                            "interview_a": a.id,
                            "interview_b": b.id,
                            "description": f"{key_type.capitalize()} conflict on Day {a.day} between interview {a.id} ({a.start_minutes}-{a.end_minutes}m) and {b.id} ({b.start_minutes}-{b.end_minutes}m)."
                        })

        for s_key, items in student_day_map.items():
            find_overlaps(items, "student", "student_conflicts")

        for r_key, items in room_day_map.items():
            find_overlaps(items, "room", "room_conflicts")

        for p_key, items in panel_day_map.items():
            find_overlaps(items, "panel", "panel_conflicts")

        total_violations = sum(summary.values())
        is_valid = (total_violations == 0)

        return ValidationReport(is_valid=is_valid, violations=violations, summary=summary)
