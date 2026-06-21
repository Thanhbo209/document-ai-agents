from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Rag Platform")
    service_name: str = Field(default="rag-platform-api")
    environment: str = Field(default="local")
    debug: bool = Field(default=True)
    api_version: str = Field(default="v1")
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="text")
    metrics_enabled: bool = Field(default=True)

    # Upload
    upload_dir: str = Field(default="storage/uploads")
    artifact_dir: str = Field(default="storage/artifacts")
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024)

    chunk_max_tokens: int = Field(default=300)
    chunk_overlap_tokens: int = Field(default=40)

    ocr_enabled: bool = Field(default=True)
    ocr_low_confidence_threshold: float = Field(default=0.65)

    media_async_enabled: bool = Field(default=True)
    media_max_sync_size_bytes: int = Field(default=10 * 1024 * 1024)
    whisper_model_name: str = Field(default="base")

    connector_web_allowed_domains: list[str] = Field(default_factory=list)
    connector_web_blocked_domains: list[str] = Field(default_factory=list)
    connector_web_max_response_bytes: int = Field(default=2_000_000)
    connector_web_timeout_seconds: float = Field(default=10.0)

    repo_ingestion_max_files: int = Field(default=500)
    repo_ingestion_max_total_bytes: int = Field(default=20_000_000)
    repo_ingestion_max_file_bytes: int = Field(default=500_000)

    # tests and local boot should work without Docker using SQLite
    database_url: str = Field(default="sqlite:///./rag_platform.db")

    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    jwt_secret_key: str = Field(default="dev-change-me")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60 * 24)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RAG_PLATFORM_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
