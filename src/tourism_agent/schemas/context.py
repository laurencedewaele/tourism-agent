"""Contexte d'exécution du graphe : paramètres statiques d'un run, hors état de la conversation."""
import os
from dataclasses import dataclass

@dataclass
class Context:
    # Par défaut, le modèle est lu dans la variable d'environnement MODEL_NAME ;
    # il peut être surchargé pour un run (Studio, API, tests) via `context={"model_name": ...}`.
    model_name: str = os.environ["MODEL_NAME"]
