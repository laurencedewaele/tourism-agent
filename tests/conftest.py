# Configure les tests asynchrones pour utiliser asyncio.
import pytest
from dotenv import load_dotenv

# Sous `langgraph dev`, le .env est chargé via langgraph.json ; pytest n'en profite pas,
# on le charge donc ici, avant l'import des modules de test.
load_dotenv()

@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
