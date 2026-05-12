from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Knowledge Evolution Platform"
    ai_provider: str = "mock"
    ai_model: str | None = None
    ai_api_base: str | None = None
    ai_api_key: str | None = None
    ai_temperature: float = 0.2
    ai_max_tokens: int = 2000
    ai_timeout_seconds: float = 30
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str = "knowledge-ai"
    minio_secure: bool = False

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), env_prefix="KNOWLEDGE_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
