from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Rag Platform")
    environment: str = Field(default="local")
    debug: bool = Field(default=True)
    api_version: str = Field(default="v1")

    # tests and local boot should work without Docker using SQLite
    database_url: str = Field(default="sqlite:///./rag_platform.db")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RAG_PLATFORM_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()