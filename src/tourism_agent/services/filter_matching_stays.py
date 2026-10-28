import json
import logging
from functools import lru_cache
from pathlib import Path

from ..exceptions import CatalogError
from ..schemas.criteria import CriteriaIdentificationResult, StayType

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "data.json"


# Chargé au premier besoin puis mis en cache.
@lru_cache
def load_catalog(path: Path = DATA_PATH) -> list[dict]:
    """Charge le catalogue des séjours, en écartant les entrées mal formées."""
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise CatalogError(f"Catalogue des séjours illisible : {path}") from e
    except json.JSONDecodeError as e:
        raise CatalogError(f"Catalogue des séjours au format JSON invalide : {path} ({e})") from e

    if not isinstance(data, list):
        raise CatalogError(f"Le catalogue doit être une liste de séjours : {path}")

    stays = []
    for index, item in enumerate(data):
        if not isinstance(item, dict) or not isinstance(item.get("nom"), str):
            logger.warning("Séjour n°%d ignoré : entrée mal formée ou sans 'nom' (%r)", index, item)
            continue
        stays.append(item)
    return stays


def filter_matching_stays(criteria: CriteriaIdentificationResult) -> list[dict]:
    """Recherche dans le catalogue les séjours correspondant aux préférences du client.

    Args:
        criteria: les critères de séjour du client. Chaque critère indique un type de séjour
            (plage, campagne, montagne, ville, sport, détente, accessibleHandicap)
            et un avis : True (souhaité), False (non souhaité) ou None (non mentionné).
            Seuls les critères avec un avis True sont pris en compte pour le filtrage.

    Returns:
        Une liste de séjours, triée par pertinence. Chaque séjour contient :
        - "nom" : le nom du séjour,
        - "match" : "parfait" si tous les critères souhaités sont satisfaits,
          "partiel" si seulement une partie l'est,
        - "score" : nombre de critères satisfaits sur le nombre de critères souhaités (ex. "2/3").
        Les séjours ne satisfaisant aucun critère sont exclus. Si aucun critère n'est
        souhaité, tous les séjours sont renvoyés avec le match "parfait".

    Raises:
        CatalogError: si le catalogue des séjours ne peut pas être chargé.
    """
    catalog = load_catalog()
    criteria_dict = criteria.as_dict()
    # Récupération des critères validés positivement (avis == True)
    active_criteria = [key for key, details in criteria_dict.items() if details.get("avis") is True]

    if not active_criteria:
        # Si aucun critère n'est actif, tous les séjours sont des matchs parfaits de base
        # Le modèle analysera ensuite la pertinence de chaque séjour.
        return [{"nom": item["nom"], "match": "parfait", "score": "N/A"} for item in catalog]

    results = []
    total_criteria = len(active_criteria)

    for item in catalog:
        matched_count = 0
        for criterion in active_criteria:
            if criterion == StayType.ACCESS:
                if item.get("accessibleHandicap") == "oui":
                    matched_count += 1
            else:
                if criterion.value in (item.get("labels") or []):
                    matched_count += 1

        if matched_count > 0:
            status = "parfait" if matched_count == total_criteria else "partiel"
            results.append((matched_count, {
                "nom": item["nom"],
                "match": status,
                "score": f"{matched_count}/{total_criteria}"
            }))

    # Tri par nombre de critères satisfaits décroissant (entier, et non la chaîne "2/3"),
    # les matchs parfaits ayant le plus grand nombre arrivent naturellement en tête
    results.sort(key=lambda x: x[0], reverse=True)
    return [stay for _, stay in results]
