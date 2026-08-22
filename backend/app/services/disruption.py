from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import Company, Student, Panel, Interview
from app.services.replanner import ReplanningService

class DisruptionSimulatorService:
    @staticmethod
    def run_live_defense_scenario(db: Session, parent_version_id: int) -> Dict[str, Any]:
        """
        Executes the exact Mirai Labs Live Defense Scenario with clean version lineage (v1 -> v2 -> v3 -> v4):
        1. Step 1: Biggest Day-1 Mass Recruiter (TCS Digital) delayed by 3 hours (Parent v1 -> Child v2).
        2. Step 2: One of its panels (C01-P1) drops out (Parent v2 -> Child v3).
        3. Step 3: 15 active students withdraw simultaneously in batch (Parent v3 -> Child v4).
        """
        day1_mass = db.query(Company).filter(Company.placement_day == 1, Company.company_type == "Mass Recruiter").first()
        if not day1_mass:
            day1_mass = db.query(Company).filter(Company.placement_day == 1).first()
        
        comp_id = day1_mass.id if day1_mass else "C01"

        panel = db.query(Panel).filter(Panel.company_id == comp_id, Panel.status == "active").first()
        panel_id = panel.id if panel else f"{comp_id}-P1"

        # Step 1: Apply Company Delay (Parent: v1 -> Child: v2)
        res1 = ReplanningService.apply_disruption_and_replan(
            db=db,
            parent_version_id=parent_version_id,
            disruption_type="company_delay",
            payload={"company_id": comp_id, "delay_hours": 3.0, "effective_day": 1}
        )
        v2_id = res1["version_id"]

        # Step 2: Apply Panel Drop (Parent: v2 -> Child: v3)
        res2 = ReplanningService.apply_disruption_and_replan(
            db=db,
            parent_version_id=v2_id,
            disruption_type="panel_drop",
            payload={"company_id": comp_id, "panel_id": panel_id, "effective_day": 1, "effective_time_mins": 0}
        )
        v3_id = res2["version_id"]

        # Dynamically query active scheduled students in v3 for withdrawal step
        scheduled_ivs_v3 = db.query(Interview).filter(
            Interview.version_id == v3_id,
            Interview.status.in_(["scheduled", "rescheduled"])
        ).all()
        scheduled_stud_ids_v3 = list(dict.fromkeys([iv.student_id for iv in scheduled_ivs_v3]))
        withdrawing_stud_ids = scheduled_stud_ids_v3[:15] if len(scheduled_stud_ids_v3) >= 15 else scheduled_stud_ids_v3

        # Step 3: Apply Student Withdrawals in batch (Parent: v3 -> Child: v4)
        res3 = ReplanningService.apply_disruption_and_replan(
            db=db,
            parent_version_id=v3_id,
            disruption_type="student_withdrawal",
            payload={"student_ids": withdrawing_stud_ids, "effective_day": 1, "effective_time_mins": 0}
        )
        v4_id = res3["version_id"]

        comp_name = day1_mass.name if day1_mass else "Mass Recruiter"
        return {
            "scenario": "Mirai Labs Live Defense Scenario",
            "company_delayed": f"{comp_name} ({comp_id}) delayed by 3h",
            "panel_dropped": panel_id,
            "students_withdrawn_count": len(withdrawing_stud_ids),
            "step1_version_id": v2_id,
            "step2_version_id": v3_id,
            "final_version_id": v4_id,
            "step1_result": res1,
            "step2_result": res2,
            "result": res3
        }
