import logging
from datetime import date
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.runtime import Runtime
from ..schemas.context import Context
from ..llm import LLM_ERRORS, get_model
from ..schemas.state import State
from ..prompts.prompts import STAYS_PROPOSAL_PROMPT_DICT, get_system_prompt
from ..tools.availability_tool import PROPOSAL_TOOLS

logger = logging.getLogger(__name__)

def build_fallback_proposal(matching_stays: list[dict]) -> str:
    """Réponse construite sans LLM, utilisée lorsque le modèle est indisponible."""
    if not matching_stays:
        return ("Je rencontre un problème technique et ne trouve pas de séjour correspondant "
                "à vos critères pour le moment. Pourriez-vous réessayer dans quelques instants ?")
    stays = "\n".join(f"- {stay['nom']} (correspondance {stay['match']})" for stay in matching_stays)
    return ("Je rencontre un problème technique pour détailler ma proposition, mais voici "
            f"les séjours de notre catalogue qui correspondent à vos critères :\n\n{stays}")


def tools_used_this_turn(messages: list[BaseMessage]) -> bool:
    """Indique si un outil a déjà été exécuté depuis le dernier message du client."""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return False
        if isinstance(message, ToolMessage):
            return True
    return False


def respond_with_proposal_node(state: State, runtime: Runtime[Context]) -> dict:
    # Contexte par défaut (MODEL_NAME) si aucun contexte n'est fourni à l'appel du graphe
    model_name = (runtime.context or Context()).model_name

    # Récupération du prompt système pour le modèle spécifié
    # (ConfigurationError explicite si aucun prompt n'est défini pour ce modèle)
    criteria = state.get("criteria")
    matching_stays = state.get("matching_stays") or []
    travel_period = state.get("travel_period")
    system_prompt = get_system_prompt(STAYS_PROPOSAL_PROMPT_DICT, model_name) + \
                    f"\nCritères actuels : {criteria.as_dict() if criteria else {}}" + \
                    f"\nSéjours correspondants du catalogue : {matching_stays}" + \
                    f"\nPériode souhaitée par le client : {travel_period or 'non précisée'}" + \
                    f"\nDate du jour : {date.today().isoformat()}"

    messages = state.get("messages", [])
    prompt_messages = [SystemMessage(content=system_prompt)] + messages

    # Un seul passage par le nœud "tools" par tour : une fois les résultats reçus,
    # le modèle doit rédiger sa proposition sans rappeler d'outil (pas de boucle infinie)
    tools_already_used = tools_used_this_turn(messages)
    tool_choice = "none" if tools_already_used else None

    try:
        response = get_model(model_name).bind_tools(PROPOSAL_TOOLS, tool_choice=tool_choice).invoke(prompt_messages)
    except LLM_ERRORS:
        logger.exception("Échec de la rédaction de la proposition par le modèle '%s'", model_name)
        response = AIMessage(content=build_fallback_proposal(matching_stays))

    if tools_already_used and response.tool_calls:
        logger.warning("Le modèle '%s' redemande un outil après avoir reçu les résultats", model_name)
        response = AIMessage(content=build_fallback_proposal(matching_stays))

    # Si la réponse contient un appel d'outil, tools_condition oriente le flux vers le nœud "tools"
    return {"messages": [response]}
