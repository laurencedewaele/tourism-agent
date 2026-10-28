from langchain_core.messages import AIMessage, RemoveMessage
from ..schemas.state import State
from ..services.input_validation import get_input_error

def reject_input_node(state: State) -> dict:
    messages = state.get("messages") or []
    response = AIMessage(content=get_input_error(messages))

    # Le message rejeté est retiré de l'historique : sinon il serait transmis au LLM
    # lors des tours suivants (respond_with_proposal reçoit toute la conversation)
    if messages and messages[-1].id:
        return {"messages": [RemoveMessage(id=messages[-1].id), response]}
    return {"messages": [response]}
