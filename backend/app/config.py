"""Единая конфигурация из ENV (.env.example). Агент 1."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    OPENDOTA_BASE_URL: str = "https://api.opendota.com/api"
    OPENDOTA_API_KEY: str = ""
    OPENDOTA_TIMEOUT_SEC: float = 15.0
    OPENDOTA_MAX_RPS: float = 1.0
    SCORE_W_COUNTER: float = 0.55
    SCORE_W_SYNERGY: float = 0.15
    SCORE_W_ROLE: float = 0.15
    SCORE_W_META: float = 0.15
    SMOOTHING_K: float = 50.0
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "draft_scenarios"
    ENABLE_RAG: bool = False
    LLM_PROVIDER: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
