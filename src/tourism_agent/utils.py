from langchain_core.messages import BaseMessage
from tourism_agent.schemas.state import State

def pretty_print_messages(messages: list[BaseMessage]) -> None:
    """Affiche proprement une liste de messages LangGraph/LangChain."""
    print("\n" + "="*50 + "\n CONVERSATION HISTORY \n" + "="*50)

    for msg in messages:
        # Détermine le rôle / type de message
        role = msg.type.upper()

        # Gestion du nom de l'agent si disponible
        name = f" ({msg.name})" if hasattr(msg, "name") and msg.name else ""

        print(f"[{role}{name}]: {msg.content}")

        # Optionnel : Afficher les appels d'outils (tool calls) si l'IA en utilise
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                print(f"   🛠️ Tool call : {tool_call['name']}({tool_call['args']})")


def print_state(state: State) -> None:
    """Affiche le contenu du state : clés, critères (CRITERE - Avis : Justification) et messages."""
    print("=== CLÉS DISPONIBLES DANS LE STATE ===")
    print(list(state.keys()))

    print("\n=== CONTENU DU CHAMP 'criteria' ===")
    criteria_result = state.get("criteria")
    if not criteria_result or not criteria_result.criteria:
        print("Aucun critère identifié.")
    else:
        for item in criteria_result.criteria:
            justification = item.justification or "Aucune justification fournie."
            print(f"{item.criterion.name} - {item.avis} : {justification}")

    print("\n=== HISTORIQUE DES MESSAGES ===")
    pretty_print_messages(state.get("messages", []))