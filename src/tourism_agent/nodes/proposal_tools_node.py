import logging
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt.tool_node import ToolInvocationError
from ..exceptions import CatalogError
from ..tools.availability_tool import PROPOSAL_TOOLS

logger = logging.getLogger(__name__)

def handle_tool_error(e: CatalogError | ToolInvocationError) -> str:
    """Erreur renvoyée au modèle sous forme de ToolMessage (les autres exceptions sont levées)."""
    logger.error("Échec de l'outil de disponibilité : %s", e)
    return "Vérification impossible pour le moment."


# Exécute les appels d'outil demandés par respond_with_proposal ; les ToolMessage produits
# sont ajoutés à l'historique, puis le flux revient à respond_with_proposal
proposal_tools_node = ToolNode(PROPOSAL_TOOLS, handle_tool_errors=handle_tool_error)
