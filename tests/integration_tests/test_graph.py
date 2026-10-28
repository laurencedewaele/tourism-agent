import pytest
from langchain_core.messages import HumanMessage

from tourism_agent.graph import graph
from tourism_agent.schemas.criteria import StayType

pytestmark = pytest.mark.anyio

def _positive_criteria(state: dict) -> set[StayType]:
    return {c.criterion for c in state["criteria"].criteria if c.avis is True}


async def test_criteria_enriched_across_turns() -> None:
    # Tour 1 : Montpellier, repos, plage
    state = await graph.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content="J'aimerais bien passer quelques jours à Montpellier "
                    "pour me reposer et profiter de la plage."
                )
            ]
        }
    )
    positives = _positive_criteria(state)
    assert {StayType.CITY, StayType.RELAX, StayType.BEACH} <= positives
    assert StayType.ACCESS not in positives

    # Tour 2 : on continue la conversation avec l'état existant et on ajoute l'accessibilité
    state["messages"].append(
        HumanMessage(
            content="En fait, j'ai aussi besoin que le logement soit accessible en fauteuil roulant."
        )
    )
    state = await graph.ainvoke(state)
    positives = _positive_criteria(state)
    assert {StayType.CITY, StayType.RELAX, StayType.BEACH, StayType.ACCESS} <= positives


async def test_travel_period_and_availability() -> None:
    # Chamonix option ski n'est pas disponible en juillet 2027, la randonnée en Lozère l'est
    state = await graph.ainvoke(
        {"messages": [HumanMessage(content="Je cherche un séjour sportif à la montagne en juillet 2027.")]}
    )
    assert "juillet" in (state.get("travel_period") or "").lower()
    assert "Lozère" in state["messages"][-1].text
