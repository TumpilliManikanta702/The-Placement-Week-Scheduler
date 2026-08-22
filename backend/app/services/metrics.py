from typing import Dict, Any
from sqlalchemy.orm import Session
from app.config import config
from app.database.models import Interview, Room, Panel, Student, Company
from app.services.validator import ScheduleValidator
from app.services.diff_engine import DiffEngine

class MetricsEngine:
    @staticmethod
    def calculate_metrics(db: Session, version_id: int, parent_version_id: int = None) -> Dict[str, Any]:
        interviews = db.query(Interview).filter(Interview.version_id == version_id).all()
        total_interviews = len(interviews)
        
        scheduled = [iv for iv in interviews if iv.status in ["scheduled", "rescheduled"]]
        unscheduled = [iv for iv in interviews if iv.status == "unscheduled"]
        cancelled = [iv for iv in interviews if iv.status in ["cancelled", "withdrawn"]]

        scheduled_count = len(scheduled)
        unscheduled_count = len(unscheduled)
        cancelled_count = len(cancelled)

        scheduling_rate = round((scheduled_count / total_interviews * 100.0), 2) if total_interviews > 0 else 0.0

        # Validate for clashes
        val_report = ScheduleValidator.validate_version(db, version_id)
        clash_count = val_report.summary.get("student_conflicts", 0) + val_report.summary.get("room_conflicts", 0) + val_report.summary.get("panel_conflicts", 0)

        # Room utilization
        rooms_count = db.query(Room).filter(Room.status == "available").count()
        total_available_room_mins = rooms_count * config.NUM_DAYS * config.WORKING_MINUTES_PER_DAY
        total_occupied_room_mins = sum(iv.end_minutes - iv.start_minutes for iv in scheduled if iv.end_minutes and iv.start_minutes)
        room_utilization = round((total_occupied_room_mins / total_available_room_mins * 100.0), 2) if total_available_room_mins > 0 else 0.0

        # Panel utilization
        active_panels_count = db.query(Panel).filter(Panel.status == "active").count()
        total_available_panel_mins = active_panels_count * config.NUM_DAYS * config.WORKING_MINUTES_PER_DAY
        panel_utilization = round((total_occupied_room_mins / total_available_panel_mins * 100.0), 2) if total_available_panel_mins > 0 else 0.0

        # Average student wait time (gap between consecutive interviews on same day)
        student_day_schedules: Dict[str, list] = {}
        for iv in scheduled:
            key = f"{iv.student_id}_D{iv.day}"
            student_day_schedules.setdefault(key, []).append(iv)

        wait_gaps = []
        for key, iv_list in student_day_schedules.items():
            if len(iv_list) > 1:
                sorted_ivs = sorted(iv_list, key=lambda x: x.start_minutes)
                for i in range(len(sorted_ivs) - 1):
                    gap = sorted_ivs[i + 1].start_minutes - sorted_ivs[i].end_minutes
                    if gap > 0:
                        wait_gaps.append(gap)

        avg_student_wait_mins = round((sum(wait_gaps) / len(wait_gaps)), 1) if wait_gaps else 0.0

        # Replan churn rate
        replan_churn_pct = 0.0
        if parent_version_id is not None:
            diff_res = DiffEngine.compute_diff(db, parent_version_id, version_id)
            replan_churn_pct = diff_res["summary"]["replan_churn_pct"]

        # Composite Quality Score (0 to 100)
        # Quality = 0.50*SchedulingRate + 0.20*RoomUtil + 0.15*PanelUtil - 5.0*Clashes - 0.5*WaitMins - 1.0*Churn
        raw_score = (
            (0.50 * scheduling_rate) +
            (0.20 * room_utilization) +
            (0.15 * panel_utilization) -
            (5.0 * clash_count) -
            (0.5 * min(avg_student_wait_mins, 60)) -
            (1.0 * replan_churn_pct)
        )
        quality_score = round(max(0.0, min(100.0, raw_score)), 1)

        return {
            "version_id": version_id,
            "total_interviews": total_interviews,
            "scheduled_count": scheduled_count,
            "unscheduled_count": unscheduled_count,
            "cancelled_count": cancelled_count,
            "scheduling_rate_pct": scheduling_rate,
            "student_clash_count": clash_count,
            "room_utilization_pct": room_utilization,
            "panel_utilization_pct": panel_utilization,
            "avg_student_wait_mins": avg_student_wait_mins,
            "replan_churn_pct": replan_churn_pct,
            "quality_score": quality_score,
            "validation_passed": val_report.is_valid
        }
