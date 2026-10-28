"""
Ce nœud génère une réponse de confirmation basée sur les critères identifiés dans l'état.
Il n'est pas implémenté dans le graphe définitif.
"""

from ..schemas.state import State
from langchain_core.messages import AIMessage

def respond_with_confirmation_node(state: State) -> dict:
    criteria = state.get("criteria")
    criteria_dict = criteria.as_dict() if criteria else {}

    # Construction dynamique et instantanée de la réponse en Python
    intro = "Si j'ai bien compris votre demande, j'ai identifié les préférences suivantes :\n\n"
    active_criteria = []
    for stay_type, details in criteria_dict.items():
        if details["avis"] is not None:
            status = "OK" if details["avis"] else "à éviter"
            active_criteria.append(f"- **{stay_type.value}** ({status}) : {details['justification']}")

    body = "\n".join(active_criteria)
    conclusion = "\n\nJe recherche dès maintenant les meilleures options correspondant à ces critères !"

    full_response = intro + body + conclusion
    return {"messages": [AIMessage(content=full_response)]}