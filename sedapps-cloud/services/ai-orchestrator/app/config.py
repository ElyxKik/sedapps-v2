from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    CORE_API_URL: str = "http://core-api:8000"
    INTERNAL_API_TOKEN: str = "change-me-internal-token"

    # ── LLM Provider ─────────────────────────────────────────────────────────────
    # Valeurs possibles : "deepseek" | "openai" | "anthropic"
    LLM_PROVIDER: str = "deepseek"
    LLM_TIMEOUT_S: int = 120
    LLM_MAX_RETRIES: int = 2

    # ── DeepSeek ──────────────────────────────────────────────────────────────────
    LLM_MODEL: str = "deepseek-v4-pro"
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_API_KEY: str = ""

    # ── OpenAI ────────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"

    # ── Anthropic (Claude) ────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com/v1"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"


settings = Settings()  # type: ignore[call-arg]
