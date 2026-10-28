import json
import logging
import re
from functools import lru_cache
from pathlib import Path

from ..exceptions import CatalogError

logger = logging.getLogger(__name__)

DISPO_PATH = Path(__file__).resolve().parent.parent / "data" / "dispo.json"

MONTH_NAMES = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
               "août", "septembre", "octobre", "novembre", "décembre"]
# Mois au format AAAAMM (ex. "202707")
MONTH_PATTERN = re.compile(r"^(\d{4})(0[1-9]|1[0-2])$")


# Chargé au premier besoin puis mis en cache.
@lru_cache
def load_availability(path: Path = DISPO_PATH) -> dict[str, list[str]]:
    """Charge les disponibilités par nom de séjour, en écartant les entrées et mois mal formés."""
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise CatalogError(f"Disponibilités des séjours illisibles : {path}") from e
    except json.JSONDecodeError as e:
        raise CatalogError(f"Disponibilités des séjours au format JSON invalide : {path} ({e})") from e

    if not isinstance(data, list):
        raise CatalogError(f"Les disponibilités doivent être une liste de séjours : {path}")

    availability = {}
    for index, item in enumerate(data):
        if (not isinstance(item, dict) or not isinstance(item.get("nom"), str)
                or not isinstance(item.get("dispos"), list)):
            logger.warning("Disponibilité n°%d ignorée : entrée mal formée (%r)", index, item)
            continue
        months = []
        for month in item["dispos"]:
            if isinstance(month, str) and MONTH_PATTERN.match(month):
                months.append(month)
            else:
                logger.warning("Mois %r ignoré pour le séjour '%s' : format AAAAMM attendu", month, item["nom"])
        availability[item["nom"]] = sorted(months)
    return availability


def format_month(month: str) -> str:
    """Convertit un mois AAAAMM en libellé lisible (ex. "202707" -> "juillet 2027")."""
    year, month_number = MONTH_PATTERN.match(month).groups()
    return f"{MONTH_NAMES[int(month_number) - 1]} {year}"


def get_stays_availability(stay_names: list[str]) -> list[dict]:
    """Donne les mois de disponibilité des séjours demandés.

    Args:
        stay_names: les noms des séjours à vérifier.

    Returns:
        Une liste avec, pour chaque séjour :
        - "nom" : le nom du séjour,
        - "mois_disponibles" : les mois disponibles sous forme lisible (ex. "juillet 2027"),
          ou None si le séjour n'a pas de disponibilités renseignées.

    Raises:
        CatalogError: si les disponibilités ne peuvent pas être chargées.
    """
    availability = load_availability()
    return [
        {
            "nom": name,
            "mois_disponibles": [format_month(month) for month in availability[name]]
            if name in availability else None,
        }
        for name in stay_names
    ]
