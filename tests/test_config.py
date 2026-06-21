from app.core.config import Settings


def test_settings_have_safe_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "Rag Platform"
    assert settings.service_name == "rag-platform-api"
    assert settings.environment == "local"
    assert settings.debug is True
    assert settings.api_version == "v1"
    assert settings.log_level == "INFO"
    assert settings.log_format == "text"
    assert settings.metrics_enabled is True
    assert settings.database_url == "sqlite:///./rag_platform.db"
    assert settings.upload_dir == "storage/uploads"
    assert settings.max_upload_size_bytes == 10 * 1024 * 1024
    assert settings.chunk_max_tokens == 300
    assert settings.chunk_overlap_tokens == 40


def test_settings_can_be_overridden() -> None:
    settings = Settings(
        app_name="Test Rag Platform",
        service_name="test-service",
        environment="test",
        debug=False,
        api_version="test-v1",
        log_level="DEBUG",
        log_format="json",
        metrics_enabled=False,
        database_url="sqlite:///./test.db",
        upload_dir="tmp/uploads",
        max_upload_size_bytes=123,
        chunk_max_tokens=123,
        chunk_overlap_tokens=12,
    )

    assert settings.app_name == "Test Rag Platform"
    assert settings.service_name == "test-service"
    assert settings.environment == "test"
    assert settings.debug is False
    assert settings.api_version == "test-v1"
    assert settings.log_level == "DEBUG"
    assert settings.log_format == "json"
    assert settings.metrics_enabled is False
    assert settings.database_url == "sqlite:///./test.db"
    assert settings.upload_dir == "tmp/uploads"
    assert settings.max_upload_size_bytes == 123
    assert settings.chunk_max_tokens == 123
    assert settings.chunk_overlap_tokens == 12
