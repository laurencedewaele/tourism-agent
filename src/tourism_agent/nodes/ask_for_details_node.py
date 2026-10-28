from ..schemas.state import State
from ..schemas.criteria import StayType
from langchain_core.messages import AIMessage

def ask_for_details_node(state: State) -> dict:
    # Récupération des libellés des types de séjour disponibles, sous forme de liste à puces
    # (séparateur dédié : certains libellés contiennent eux-mêmes une virgule)
    formatted_stay_types = "- " + StayType.infos(separator="\n- ")

    # Template statique
    full_response = (
        "Bonjour ! Pour que je puisse vous proposer le séjour idéal, j'ai besoin de quelques précisions sur vos envies.\n"
        "Pourriez-vous m'indiquer vos préférences parmi les choix suivants :\n\n"
        f"{formatted_stay_types}\n"
    )
    return {"messages": [AIMessage(content=full_response)]}