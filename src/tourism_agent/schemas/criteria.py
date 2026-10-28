from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# Définition de StayType avec une valeur technique et un libellé personnalisé
class StayType(str, Enum):
    BEACH = ("plage", "en bord de mer, à la plage")
    COUNTRYSIDE = ("campagne", "à la campagne")
    MOUNTAINS = ("montagne", "à la montagne")
    CITY = ("ville", "en ville")
    SPORT = ("sport", "activités sportives")
    RELAX = ("détente", "détente")
    ACCESS = ("accessibleHandicap", "accessibilité pour personne handicapée ou à mobilité réduite")

    # Surcharge du constructeur
    def __new__(cls, tech_id, label):
        obj = str.__new__(cls, tech_id)
        obj._value_ = tech_id
        obj.label = label
        return obj

    @classmethod
    def infos(cls, separator: str = ", ") -> str:
        return separator.join(stay.label for stay in cls)

class CriterionOpinion(BaseModel):
    """Avis exprimé par l'utilisateur ou détecté selon ses préférences de destination et d'activité."""

    criterion: StayType = Field(description="Type de séjour concerné.")
    avis: Optional[bool] = Field(
        default=None,
        description="True si un avis positif est détecté, False s'il est négatif, None si non mentionné."
    )
    justification: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Justification brève et informelle de ton positionnement (100 caractères maximum)"
    )

class CriteriaIdentificationResult(BaseModel):
    """Critères de séjour identifiés dans le message de l'utilisateur."""

    criteria: Optional[list[CriterionOpinion]] = Field(
        default=None,
        description="Un élément pour chaque type de séjour détecté.",
    )
    travel_period: Optional[str] = Field(
        default=None,
        description="Période ou mois où le client projette son séjour, tels qu'il les a exprimés "
                    "(ex. « juillet-août 2027 », « pendant les vacances de Noël »). None si non mentionné.",
    )

    # Indique si au moins un avis positif a été identifié parmi les critères.
    @property
    def details_identified(self) -> bool:
        if not self.criteria:
            return False
        return any(c.avis is True for c in self.criteria)

    # Transforme le résultat en dictionnaire pour un accès facile par type de séjour.
    def as_dict(self) -> dict[StayType, dict]:
        if not self.criteria:
            return {}
        return {c.criterion: {"avis": c.avis, "justification": c.justification} for c in self.criteria}
