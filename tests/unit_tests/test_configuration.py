from langgraph.pregel import Pregel
# Pregel est le moteur d’exécution qui orchestre les étapes et les boucles d’un graphe LangGraph.
from tourism_agent.graph import graph

def test_graph_compiles() -> None:
    """Vérifie que le graphe de l'agent de tourisme compile correctement en un objet Pregel."""
    assert isinstance(graph, Pregel)
