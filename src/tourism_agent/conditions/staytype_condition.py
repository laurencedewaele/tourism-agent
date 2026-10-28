from typing import Literal
from ..schemas.state import State

def staytype_condition(state: State) -> Literal["criteria_detected", "need_details"]:
    # Utilise la propriété details_identified pour l'aiguillage
    # (critères absents, par exemple après un échec de l'analyse : on demande des précisions)
    criteria = state.get("criteria")
    if criteria is not None and criteria.details_identified:
        return "criteria_detected"
    else:
        return "need_details"
