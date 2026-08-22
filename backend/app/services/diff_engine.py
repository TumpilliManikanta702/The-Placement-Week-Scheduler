from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Interview, Student, Company, Room, Panel

class DiffEngine:
    @staticmethod
    def compute_diff(db: Session, old_version_id: int, new_version_id: int) -> Dict[str, Any]:
        old_interviews = db.query(Interview).filter(Interview.version_id == old_version_id).all()
        new_interviews = db.query(Interview).filter(Interview.version_id == new_version_id).all()

        # Map by unique interview suffix key (e.g. "0001") for 1-to-1 precise matching
        old_suffix_map = {iv.id.split('-')[-1]: iv for iv in old_interviews}
        new_suffix_map = {iv.id.split('-')[-1]: iv for iv in new_interviews}

        students = {s.id: s for s in db.query(Student).all()}
        companies = {c.id: c for c in db.query(Company).all()}
        rooms = {r.id: r for r in db.query(Room).all()}
        panels = {p.id: p for p in db.query(Panel).all()}

        summary = {
            "unchanged": 0,
            "moved": 0,
            "cancelled": 0,
            "newly_scheduled": 0,
            "room_changes": 0,
            "panel_changes": 0,
            "time_changes": 0,
            "day_changes": 0,
            "total_evaluated": len(new_suffix_map)
        }

        diff_details = []

        for suffix, new_iv in new_suffix_map.items():
            old_iv = old_suffix_map.get(suffix)
            stud = students.get(new_iv.student_id)
            comp = companies.get(new_iv.company_id)

            stud_name = stud.name if stud else new_iv.student_id
            comp_name = comp.name if comp else new_iv.company_id

            if not old_iv:
                if new_iv.status in ["scheduled", "rescheduled"]:
                    summary["newly_scheduled"] += 1
                    diff_details.append({
                        "interview_id": new_iv.id,
                        "student_id": new_iv.student_id,
                        "student_name": stud_name,
                        "company_id": new_iv.company_id,
                        "company_name": comp_name,
                        "change_type": "NEWLY_SCHEDULED",
                        "old": None,
                        "new": DiffEngine._format_schedule_info(new_iv, rooms, panels),
                        "reason": new_iv.change_reason or "Initial schedule creation"
                    })
                continue

            # Compare statuses
            old_sched = old_iv.status in ["scheduled", "rescheduled"]
            new_sched = new_iv.status in ["scheduled", "rescheduled"]

            if old_sched and not new_sched:
                summary["cancelled"] += 1
                diff_details.append({
                    "interview_id": new_iv.id,
                    "student_id": new_iv.student_id,
                    "student_name": stud_name,
                    "company_id": new_iv.company_id,
                    "company_name": comp_name,
                    "change_type": "CANCELLED",
                    "old": DiffEngine._format_schedule_info(old_iv, rooms, panels),
                    "new": {"status": new_iv.status, "refusal_reason": new_iv.refusal_reason},
                    "reason": new_iv.change_reason or "Disruption / Capacity constraint"
                })
            elif not old_sched and new_sched:
                summary["newly_scheduled"] += 1
                diff_details.append({
                    "interview_id": new_iv.id,
                    "student_id": new_iv.student_id,
                    "student_name": stud_name,
                    "company_id": new_iv.company_id,
                    "company_name": comp_name,
                    "change_type": "NEWLY_SCHEDULED",
                    "old": {"status": old_iv.status},
                    "new": DiffEngine._format_schedule_info(new_iv, rooms, panels),
                    "reason": new_iv.change_reason or "Capacity freed during replan"
                })
            elif old_sched and new_sched:
                # Both scheduled - check for changes
                day_changed = (old_iv.day != new_iv.day)
                time_changed = (old_iv.start_minutes != new_iv.start_minutes)
                room_changed = (old_iv.room_id != new_iv.room_id)
                panel_changed = (old_iv.panel_id != new_iv.panel_id)

                if not (day_changed or time_changed or room_changed or panel_changed):
                    summary["unchanged"] += 1
                else:
                    summary["moved"] += 1
                    changes = []
                    if day_changed:
                        summary["day_changes"] += 1
                        changes.append("Day")
                    if time_changed:
                        summary["time_changes"] += 1
                        changes.append("Time")
                    if room_changed:
                        summary["room_changes"] += 1
                        changes.append("Room")
                    if panel_changed:
                        summary["panel_changes"] += 1
                        changes.append("Panel")

                    diff_details.append({
                        "interview_id": new_iv.id,
                        "student_id": new_iv.student_id,
                        "student_name": stud_name,
                        "company_id": new_iv.company_id,
                        "company_name": comp_name,
                        "change_type": "MOVED",
                        "changes": changes,
                        "old": DiffEngine._format_schedule_info(old_iv, rooms, panels),
                        "new": DiffEngine._format_schedule_info(new_iv, rooms, panels),
                        "reason": new_iv.change_reason or "Replan optimization shift"
                    })

        previously_scheduled = sum(1 for iv in old_interviews if iv.status in ["scheduled", "rescheduled"])
        changed_count = summary["moved"] + summary["cancelled"]
        replan_churn_pct = round((changed_count / max(previously_scheduled, 1)) * 100.0, 2)
        summary["previously_scheduled"] = previously_scheduled
        summary["replan_churn_pct"] = replan_churn_pct

        return {
            "old_version_id": old_version_id,
            "new_version_id": new_version_id,
            "summary": summary,
            "diff_details": diff_details
        }

    @staticmethod
    def _format_schedule_info(iv: Interview, rooms: Dict[str, Room], panels: Dict[str, Panel]) -> Dict[str, Any]:
        room = rooms.get(iv.room_id)
        panel = panels.get(iv.panel_id)
        start_time_formatted = f"{(iv.start_minutes // 60) + 9:02d}:{iv.start_minutes % 60:02d}" if iv.start_minutes is not None else None
        end_time_formatted = f"{(iv.end_minutes // 60) + 9:02d}:{iv.end_minutes % 60:02d}" if iv.end_minutes is not None else None

        return {
            "status": iv.status,
            "day": iv.day,
            "start_minutes": iv.start_minutes,
            "end_minutes": iv.end_minutes,
            "start_time": start_time_formatted,
            "end_time": end_time_formatted,
            "room_id": iv.room_id,
            "room_name": room.name if room else iv.room_id,
            "panel_id": iv.panel_id,
            "panel_name": panel.id if panel else iv.panel_id
        }
