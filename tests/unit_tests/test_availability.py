"""Disponibilités des séjours et appel de l'outil par le modèle (sans appel réseau : le modèle est simulé)."""
import json
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.runtime import Runtime
from tourism_agent.exceptions import CatalogError
from tourism_agent.graph import graph
from tourism_agent.nodes import analyze_preferences_node as analyze_module
from tourism_agent.nodes import respond_with_proposal_node as proposal_module
from tourism_agent.prompts.prompts import STAYS_PROPOSAL_PROMPT_DICT
from tourism_agent.schemas.context import Context
from tourism_agent.schemas.criteria import CriteriaIdentificationResult, CriterionOpinion, StayType
from tourism_agent.services import availability as service

MODEL_NAME = next(iter(STAYS_PROPOSAL_PROMPT_DICT))
CONTEXT = Context(model_name=MODEL_NAME)
MOUNTAIN_CRITERIA = CriteriaIdentificationResult(
    criteria=[CriterionOpinion(criterion=StayType.MOUNTAINS, avis=True)],
    travel_period="juillet 2027",
)


class ToolCallingModel:
    """Faux modèle de chat : analyse fixe des préférences, puis appel de l'outil de
    disponibilité tant qu'aucun résultat d'outil n'a été reçu pour ce tour."""

    def __init__(self):
        self.tool_choices = []

    def with_structured_output(self, schema):
        return self.StructuredOutput()

    class StructuredOutput:
        def invoke(self, messages):
            return MOUNTAIN_CRITERIA

    def bind_tools(self, tools, tool_choice=None):
        self.tool_choices.append(tool_choice)
        return self

    def invoke(self, messages):
        if isinstance(messages[-1], ToolMessage):
            return AIMessage(content="Réponse finale")
        return AIMessage(content="", tool_calls=[{
            "name": "check_stays_availability",
            "args": {"stay_names": ["Randonnée camping en Lozère"]},
            "id": "call-1",
        }])


@pytest.fixture
def tool_calling_model(monkeypatch):
    """Fixture qui remplace le modèle par un modèle simulé appelant l'outil."""
    model = ToolCallingModel()
    for module in (analyze_module, proposal_module):
        monkeypatch.setattr(module, "get_model", lambda model_name: model)
    return model


def test_load_availability_missing_file(tmp_path) -> None:
    """Vérifie que le chargement d'un fichier de disponibilités inexistant lève une `CatalogError`."""
    with pytest.raises(CatalogError):
        service.load_availability(tmp_path / "absent.json")


def test_load_availability_invalid_json(tmp_path) -> None:
    """Vérifie que le chargement d'un fichier JSON invalide lève une `CatalogError`."""
    path = tmp_path / "dispo.json"
    path.write_text("{ pas du json", encoding="utf-8")
    with pytest.raises(CatalogError):
        service.load_availability(path)


def test_load_availability_skips_malformed_entries_and_months(tmp_path) -> None:
    """Vérifie que les entrées mal formées et les mois au mauvais format sont ignorés."""
    path = tmp_path / "dispo.json"
    path.write_text(json.dumps([
        {"nom": "Séjour valide", "dispos": ["202708", "2027-07", "202713", 202709, "202707"]},
        {"nom": "Sans dispos"},
        {"dispos": ["202707"]},
    ]), encoding="utf-8")
    assert service.load_availability(path) == {"Séjour valide": ["202707", "202708"]}


def test_get_stays_availability_known_and_unknown_stays(monkeypatch) -> None:
    """Vérifie que les mois sont rendus lisibles et qu'un séjour sans disponibilités renvoie None."""
    monkeypatch.setattr(service, "load_availability", lambda: {"Séjour connu": ["202612", "202701"]})
    assert service.get_stays_availability(["Séjour connu", "Séjour inconnu"]) == [
        {"nom": "Séjour connu", "mois_disponibles": ["décembre 2026", "janvier 2027"]},
        {"nom": "Séjour inconnu", "mois_disponibles": None},
    ]


def test_tools_used_this_turn_ignores_previous_turns() -> None:
    """Vérifie que seuls les résultats d'outil reçus depuis le dernier message du client comptent."""
    previous_turn = [HumanMessage(content="Montagne en juillet"),
                     ToolMessage(content="[]", tool_call_id="call-0"),
                     AIMessage(content="Proposition")]
    assert not proposal_module.tools_used_this_turn(previous_turn + [HumanMessage(content="Et en août ?")])
    assert proposal_module.tools_used_this_turn(previous_turn[:2])


def test_graph_runs_tool_node_then_answers(tool_calling_model) -> None:
    """Vérifie que l'appel d'outil passe par le nœud "tools" et que ses messages restent dans l'historique."""
    state = graph.invoke({"messages": [HumanMessage(content="Montagne en juillet 2027")]}, context=CONTEXT)

    _, tool_request, tool_message, answer = state["messages"]
    assert tool_request.tool_calls[0]["name"] == "check_stays_availability"
    assert isinstance(tool_message, ToolMessage) and tool_message.tool_call_id == "call-1"
    assert "juillet 2027" in tool_message.content
    assert answer.content == "Réponse finale"
    assert state["travel_period"] == "juillet 2027"
    # Le second passage dans respond_with_proposal interdit un nouvel appel d'outil
    assert tool_calling_model.tool_choices == [None, "none"]


def test_graph_tool_failure_is_reported_to_model(tool_calling_model, monkeypatch) -> None:
    """Vérifie qu'un échec de l'outil est transmis au modèle, qui rédige tout de même sa réponse."""
    def broken_availability():
        raise CatalogError("disponibilités indisponibles")

    monkeypatch.setattr(service, "load_availability", broken_availability)
    state = graph.invoke({"messages": [HumanMessage(content="Montagne en juillet 2027")]}, context=CONTEXT)

    tool_message, answer = state["messages"][-2:]
    assert isinstance(tool_message, ToolMessage) and tool_message.status == "error"
    assert answer.content == "Réponse finale"


def test_proposal_refuses_second_tool_call(monkeypatch) -> None:
    """Vérifie qu'un nouvel appel d'outil après réception des résultats est remplacé par la réponse de secours."""
    model = ToolCallingModel()
    model.invoke = lambda messages: AIMessage(content="", tool_calls=[{
        "name": "check_stays_availability", "args": {"stay_names": []}, "id": "call-2",
    }])
    monkeypatch.setattr(proposal_module, "get_model", lambda model_name: model)
    state = {
        "messages": [HumanMessage(content="Montagne en juillet 2027"),
                     ToolMessage(content="[]", tool_call_id="call-1")],
        "matching_stays": [{"nom": "Randonnée camping en Lozère", "match": "parfait", "score": "1/1"}],
    }

    [message] = proposal_module.respond_with_proposal_node(state, Runtime(context=CONTEXT))["messages"]
    assert not message.tool_calls
    assert "Randonnée camping en Lozère" in message.content
