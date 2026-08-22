from typing import Dict, Any, List
try:
    from ortools.sat.python import cp_model
    HAS_OR_TOOLS = True
except ImportError:
    HAS_OR_TOOLS = False

class CpSatConstraintBuilder:
    """
    Builds Hard Constraints for Google OR-Tools CP-SAT Model.
    """
    @staticmethod
    def add_hard_constraints(
        cp_model_obj,
        variables: Dict[str, Dict[str, Any]],
        rooms: list,
        panels_by_company: dict,
        num_days: int = 4
    ):
        model = cp_model_obj.model

        # 1. Withdrawn Students Constraint
        for key, var_dict in variables.items():
            stud = var_dict["student"]
            if stud.is_withdrawn:
                model.Add(var_dict["scheduled"] == 0)

        # 2. Company Arrival Delay Constraint
        for key, var_dict in variables.items():
            comp = var_dict["company"]
            if comp.arrival_status == "delayed":
                delay_mins = int(comp.delay_hours * 60)
                delay_slot = delay_mins // 15
                delay_day = comp.delay_day

                # If scheduled on delay_day, start_slot >= delay_slot
                is_delay_day = model.NewBoolVar(f"is_delay_day_{key}")
                model.Add(var_dict["day"] == delay_day).OnlyEnforceIf(is_delay_day)
                model.Add(var_dict["day"] != delay_day).OnlyEnforceIf(is_delay_day.Not())
                model.Add(var_dict["start_slot"] >= delay_slot).OnlyEnforceIf([is_delay_day, var_dict["scheduled"]])

        # Group variables by Student ID
        student_vars: Dict[str, List[Dict[str, Any]]] = {}
        for key, var_dict in variables.items():
            stud_id = var_dict["student"].id
            student_vars.setdefault(stud_id, []).append(var_dict)

        # 3. Student Non-Overlap Constraints across days
        for stud_id, s_vars in student_vars.items():
            if len(s_vars) > 1:
                for i in range(len(s_vars)):
                    for j in range(i + 1, len(s_vars)):
                        v1, v2 = s_vars[i], s_vars[j]
                        # If on same day and both scheduled, intervals must not overlap
                        same_day = model.NewBoolVar(f"same_day_{stud_id}_{i}_{j}")
                        model.Add(v1["day"] == v2["day"]).OnlyEnforceIf(same_day)
                        model.Add(v1["day"] != v2["day"]).OnlyEnforceIf(same_day.Not())

                        both_scheduled = model.NewBoolVar(f"both_sched_{stud_id}_{i}_{j}")
                        model.AddBoolAnd([v1["scheduled"], v2["scheduled"], same_day]).OnlyEnforceIf(both_scheduled)

                        # Either v1 ends before v2 starts OR v2 ends before v1 starts
                        v1_before_v2 = model.NewBoolVar(f"v1_before_v2_{stud_id}_{i}_{j}")
                        model.Add(v1["end_slot"] <= v2["start_slot"]).OnlyEnforceIf(v1_before_v2)
                        model.Add(v2["end_slot"] <= v1["start_slot"]).OnlyEnforceIf(v1_before_v2.Not())

                        model.AddBoolOr([v1_before_v2, v1_before_v2.Not()]).OnlyEnforceIf(both_scheduled)
