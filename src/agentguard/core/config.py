"""Application configuration settings for AgentGuard."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "AgentGuard"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    POSTGRES_USER: str = "agentguard"
    POSTGRES_PASSWORD: str = "agentguard_dev_secret"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "agentguard"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    OTEL_SERVICE_NAME: str = "agentguard-observability"
    OTEL_ENDPOINT: str = "http://localhost:8000/api/v1/traces/ingest"

    DEFAULT_MIN_MRR: float = 0.70
    DEFAULT_MIN_PRECISION_AT_K: float = 0.60
    DEFAULT_MIN_GROUNDEDNESS: float = 0.85
    DEFAULT_MAX_CRITICAL_FAILURES: int = 0
    DEFAULT_MAX_P95_LATENCY_MS: float = 5000.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
