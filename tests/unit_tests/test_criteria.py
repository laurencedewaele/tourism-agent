from tourism_agent.schemas.criteria import StayType

def test_stay_type_infos_exists_and_returns_str() -> None:
    """Vérifie que la méthode `infos` de `StayType` existe, est callable et retourne une chaîne non vide."""
    infos = getattr(StayType, "infos", None)

    assert callable(infos)
    assert isinstance(infos(), str)
    assert infos() != ""
