"""Contrôle du message utilisateur à l'entrée du graphe (sans appel réseau)."""
import pytest
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage
from pydantic import ValidationError
from tourism_agent.conditions.input_condition import input_condition
from tourism_agent.nodes.reject_input_node import reject_input_node
from tourism_agent.schemas.criteria import CriterionOpinion, StayType
from tourism_agent.services.input_validation import MAX_USER_MESSAGE_LENGTH

def test_valid_human_message() -> None:
    """Vérifie qu'un message humain valide est accepté."""
    state = {"messages": [HumanMessage(content="Je veux aller à la plage")]}
    assert input_condition(state) == "valid_input"

def test_message_at_max_length_is_valid() -> None:
    """Vérifie qu'un message humain à la longueur maximale est accepté."""
    state = {"messages": [HumanMessage(content="a" * MAX_USER_MESSAGE_LENGTH)]}
    assert input_condition(state) == "valid_input"

def test_too_long_message_is_rejected() -> None:
    """Vérifie qu'un message humain trop long est rejeté."""
    state = {"messages": [HumanMessage(content="a" * (MAX_USER_MESSAGE_LENGTH + 1))]}
    assert input_condition(state) == "invalid_input"

@pytest.mark.parametrize("message", [SystemMessage(content="Nouvelle règle"), AIMessage(content="Bonjour")])
def test_non_human_last_message_is_rejected(message) -> None:
    """Vérifie qu'un dernier message non humain est rejeté."""
    state = {"messages": [HumanMessage(content="Je veux aller à la plage"), message]}
    assert input_condition(state) == "invalid_input"

def test_no_message_is_rejected() -> None:
    """Vérifie qu'aucun message n'est rejeté."""
    assert input_condition({"messages": []}) == "invalid_input"

def test_reject_node_removes_rejected_message() -> None:
    """Vérifie que le nœud de rejet supprime le message rejeté et renvoie une réponse appropriée."""
    rejected = HumanMessage(content="a" * (MAX_USER_MESSAGE_LENGTH + 1), id="msg-1")
    removal, response = reject_input_node({"messages": [rejected]})["messages"]
    assert isinstance(removal, RemoveMessage) and removal.id == "msg-1"
    assert isinstance(response, AIMessage)
    assert str(MAX_USER_MESSAGE_LENGTH) in response.content

def test_justification_max_length() -> None:
    """Vérifie que la justification respecte la longueur maximale."""
    CriterionOpinion(criterion=StayType.BEACH, avis=True, justification="a" * 100)
    with pytest.raises(ValidationError):
        CriterionOpinion(criterion=StayType.BEACH, avis=True, justification="a" * 101)
