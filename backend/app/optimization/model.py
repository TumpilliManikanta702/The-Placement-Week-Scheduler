from typing import Dict, Any, List, Tuple
try:
    from ortools.sat.python import cp_model
    HAS_OR_TOOLS = True
except ImportError:
    HAS_OR_TOOLS = False

class PlacementCpSatModel:
    """
    Formulates Google OR-Tools CP-SAT Decision Variables and Optional Interval Variables
    for Placement Week Scheduling.
    """
    def __init__(self):
        if not HAS_OR_TOOLS:
            raise RuntimeError("ortools package is not installed.")
        self.model = cp_model.CpModel()
        self.variables: Dict[str, Any] = {}

    def create_variables(
        self,
        shortlists: list,
        companies: dict,
        students: dict,
        rooms: list,
        panels_by_company: dict,
        num_days: int = 4,
        total_slots_per_day: int = 32,
        slot_granularity: int = 15
    ):
        model = self.model

        # Decision variables per shortlist item
        for sl in shortlists:
            comp = companies[sl.company_id]
            stud = students[sl.student_id]

            key = f"{sl.student_id}_{sl.company_id}"
            
            # 1. Scheduled boolean decision variable
            scheduled_var = model.NewBoolVar(f"sched_{key}")
            
            # 2. Day integer decision variable (1..4)
            day_var = model.NewIntVar(1, num_days, f"day_{key}")
            
            # 3. Start slot integer variable (0..32-needed)
            needed_slots = comp.interview_duration // slot_granularity
            max_start_slot = total_slots_per_day - needed_slots
            start_slot_var = model.NewIntVar(0, max_start_slot, f"start_{key}")
            end_slot_var = model.NewIntVar(needed_slots, total_slots_per_day, f"end_{key}")

            model.Add(end_slot_var == start_slot_var + needed_slots)

            self.variables[key] = {
                "scheduled": scheduled_var,
                "day": day_var,
                "start_slot": start_slot_var,
                "end_slot": end_slot_var,
                "needed_slots": needed_slots,
                "shortlist": sl,
                "company": comp,
                "student": stud
            }

        return self.variables
