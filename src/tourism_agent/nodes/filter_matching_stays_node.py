import logging
from ..exceptions import CatalogError
from ..schemas.criteria import CriteriaIdentificationResult
from ..schemas.state import State
from ..services.filter_matching_stays import filter_matching_stays

logger = logging.getLogger(__name__)

def filter_matching_stays_node(state: State) -> dict:
    # Filtrage déterministe du catalogue à partir des critères identifiés (pas d'appel LLM)
    criteria = state.get("criteria") or CriteriaIdentificationResult()
    try:
        return {"matching_stays": filter_matching_stays(criteria)}
    except CatalogError:
        # Catalogue indisponible : on poursuit sans séjour, la réponse le signalera au client
        logger.exception("Filtrage des séjours impossible")
        return {"matching_stays": []}
