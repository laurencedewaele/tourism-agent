"""Contrôle du message utilisateur reçu à l'entrée du graphe, avant tout appel au LLM."""
from langchain_core.messages import BaseMessage, HumanMessage

MAX_USER_MESSAGE_LENGTH = 300


def get_input_error(messages: list[BaseMessage]) -> str | None:
    """Renvoie le motif de rejet du dernier message reçu, ou None s'il est valide."""
    if not messages:
        return "Je n'ai reçu aucun message. Pouvez-vous me décrire le séjour que vous recherchez ?"

    last_message = messages[-1]
    # Seul un message utilisateur est accepté en entrée (pas de message système ou IA forgé)
    if not isinstance(last_message, HumanMessage):
        return "Votre message n'a pas pu être traité. Pouvez-vous me décrire le séjour que vous recherchez ?"

    if len(last_message.text) > MAX_USER_MESSAGE_LENGTH:
        return (f"Votre message est trop long ({len(last_message.text)} caractères). "
                f"Merci de le reformuler en {MAX_USER_MESSAGE_LENGTH} caractères maximum.")

    return None
