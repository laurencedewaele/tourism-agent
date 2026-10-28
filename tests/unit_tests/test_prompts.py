import os
from dotenv import load_dotenv
from tourism_agent.prompts.prompts import (
    PREFERENCES_ANALYSIS_PROMPT_DICT,
    STAYS_PROPOSAL_PROMPT_DICT,
)
"""Vérifie que les prompts existent pour le modèle configuré."""
def test_prompts_exist_for_configured_model():
    load_dotenv()
    model_name = os.environ["MODEL_NAME"]
    for prompt_dict in (
        PREFERENCES_ANALYSIS_PROMPT_DICT,
        STAYS_PROPOSAL_PROMPT_DICT,
    ):
        assert model_name in prompt_dict, (
            f"Aucun system prompt défini pour le modèle '{model_name}'"
        )
        assert prompt_dict[model_name].strip()
