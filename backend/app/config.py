from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    app_name: str = "AegisOS"
    database_url: str = "sqlite:///./aegisos.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "development-only-change-me-before-deploying"
    jwt_expire_minutes: int = 60
    workspace_root: str = "./workspaces"
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 45
    sandbox_enabled: bool = False
    sandbox_image: str = "python:3.12-slim"
    sandbox_timeout_seconds: int = 30
    sandbox_memory: str = "256m"
    sandbox_cpus: float = 1.0
    cors_origins: str = "http://localhost:5173"
    rate_limit_per_minute: int = 60

    @property
    def workspace_path(self) -> Path:
        p = Path(self.workspace_root).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

@lru_cache
def get_settings() -> Settings:
    return Settings()
