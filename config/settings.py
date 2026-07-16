"""
Central configuration. Every tunable value in the system is read from here,
which in turn reads from .env. Nothing else in the codebase should call
os.getenv() directly — add a field here instead.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "Omni-Agent SaaS"
    ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # --- LLM Provider ---
    # Placeholder by design: pick "openai" or "anthropic" in .env, fill in
    # the matching key below, and every agent switches automatically.
    LLM_PROVIDER: str = "openai"  # "openai" | "anthropic"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-sonnet-5"

    # --- Optional: enables the agents' web_search tool (serper.dev) ---
    SERPER_API_KEY: Optional[str] = None

    # --- Redis / Celery ---
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # --- PostgreSQL ---
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "omni_agent"
    POSTGRES_PASSWORD: str = "omni_agent_password"
    POSTGRES_DB: str = "omni_agent_saas"

    # --- ChromaDB ---
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION_KB: str = "knowledge_base"
    CHROMA_COLLECTION_CACHE: str = "semantic_cache"

    # --- SMTP / Email escalation ---
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SUPPORT_ESCALATION_EMAIL: Optional[str] = None

    # --- Rate limiter (token bucket) ---
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # --- Semantic cache ---
    SEMANTIC_CACHE_SIMILARITY_THRESHOLD: float = 0.92

    # --- Conversation context ---
    CONVERSATION_MAX_HISTORY_LENGTH: int = 10
    CONVERSATION_SESSION_TTL_SECONDS: int = 3600

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
