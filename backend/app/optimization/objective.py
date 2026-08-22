from typing import Dict, Any

class CpSatObjectiveBuilder:
    """
    Formulates Multi-Objective Function for Google OR-Tools CP-SAT Model.
    """
    @staticmethod
    def set_objective(cp_model_obj, variables: Dict[str, Dict[str, Any]]):
        model = cp_model_obj.model

        objective_terms = []

        for key, var_dict in variables.items():
            comp = var_dict["company"]
            sched_var = var_dict["scheduled"]
            day_var = var_dict["day"]

            # Coverage bonus (1000)
            objective_terms.append(1000 * sched_var)

            # Tier bonus (300 for tier 1, 200 for tier 2, 100 for tier 3)
            tier_bonus = 300 if comp.priority_tier == 1 else (200 if comp.priority_tier == 2 else 100)
            objective_terms.append(tier_bonus * sched_var)

            # Preferred day bonus (150)
            pref_day_var = model.NewBoolVar(f"pref_day_{key}")
            model.Add(day_var == comp.placement_day).OnlyEnforceIf(pref_day_var)
            model.Add(day_var != comp.placement_day).OnlyEnforceIf(pref_day_var.Not())
            objective_terms.append(150 * pref_day_var)

        model.Maximize(sum(objective_terms))
