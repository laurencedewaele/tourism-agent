"""Exceptions propres à l'agent de tourisme."""


class TourismAgentError(Exception):
    """Classe de base de toutes les erreurs de l'agent."""


class ConfigurationError(TourismAgentError):
    """Configuration manquante ou invalide (variable d'environnement, prompt absent...).

    Erreur de déploiement : elle n'est pas rattrapée par les nœuds, l'agent doit échouer
    immédiatement avec un message explicite.
    """


class CatalogError(TourismAgentError):
    """Catalogue des séjours introuvable ou illisible."""
