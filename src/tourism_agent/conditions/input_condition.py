from typing import Literal
from ..schemas.state import State
from ..services.input_validation import get_input_error

def input_condition(state: State) -> Literal["valid_input", "invalid_input"]:
    # Aiguillage à l'entrée du graphe : le message n'est transmis au LLM que s'il est valide
    if get_input_error(state.get("messages") or []) is None:
        return "valid_input"
    else:
        return "invalid_input"
