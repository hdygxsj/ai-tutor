from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://ai_dream:ai_dream@localhost:5432/ai_dream"
    default_tenant_id: str = "default"
    default_workspace_id: str = "default"
    tutor_ssl_verify: bool = True
    artifact_root: str = "artifacts"


@lru_cache
def get_settings() -> Settings:
    return Settings()
