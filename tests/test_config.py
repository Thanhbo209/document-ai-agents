from app.core.config import Settings


def test_settings_have_safe_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "Rag Platform"
    assert settings.environment == "local"
    assert settings.debug is True
    assert settings.api_version == "v1"
    assert settings.database_url == "sqlite:///./rag_platform.db"


def test_settings_can_be_overridden() -> None:
    settings = Settings(
        app_name="Test Rag Platform",
        environment="test",
        debug=False,
        api_version="test-v1",
        database_url="sqlite:///./test.db",
    )

    assert settings.app_name == "Test Rag Platform"
    assert settings.environment == "test"
    assert settings.debug is False
    assert settings.api_version == "test-v1"
    assert settings.database_url == "sqlite:///./test.db"