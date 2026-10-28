"""Modèles de chat partagés par les nœuds du graphe."""
import os
from functools import lru_cache
import openai
from langchain.chat_models import init_chat_model
from langchain_core.exceptions import ModelError, OutputParserException
from langchain_core.language_models import BaseChatModel
from langchain_openai.chat_models.base import OpenAIRefusalError
from pydantic import ValidationError

# Erreurs « attendues » lors d'un appel au LLM, que les nœuds rattrapent pour répondre
# en mode dégradé : réseau, délai dépassé, quota, erreur serveur (après les tentatives
# automatiques), refus du modèle ou sortie structurée non conforme au schéma.
LLM_ERRORS: tuple[type[Exception], ...] = (
    openai.OpenAIError,
    ModelError,
    OpenAIRefusalError,
    OutputParserException,
    ValidationError,
)

# Un modèle par nom, instancié une seule fois puis réutilisé d'un run à l'autre
@lru_cache
def get_model(model_name: str) -> BaseChatModel:
    # Initialisation du modèle de chat avec OpenRouter
    return init_chat_model(
        model=model_name,
        model_provider="openai",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0,
        max_retries=3,
        timeout=60,
        # Sous `langgraph dev` (stream_mode "messages"), with_structured_output passe en
        # streaming et l'usage des tokens est perdu : LangSmith n'affiche alors aucun token.
        disable_streaming=True
    )
