"""Outil mis à disposition du LLM qui rédige la proposition de séjours."""
from langchain_core.tools import tool
from ..services.availability import get_stays_availability


# La docstring est la description de l'outil transmise au LLM
@tool
def check_stays_availability(stay_names: list[str]) -> list[dict]:
    """Donne les mois de disponibilité des séjours du catalogue.

    À appeler lorsque le client a indiqué une période ou des mois pour son séjour,
    avec les noms exacts des séjours correspondant à ses critères.

    Args:
        stay_names: noms exacts des séjours à vérifier.

    Returns:
        Pour chaque séjour, "nom" et "mois_disponibles" : la liste des mois où il est
        disponible (ex. "juillet 2027"), ou null si l'on n'a pas encore d'information
        sur sa disponibilité.
    """
    return get_stays_availability(stay_names)


# Outils que le modèle peut appeler en rédigeant sa proposition (exécutés par le nœud "tools")
PROPOSAL_TOOLS = [check_stays_availability]
