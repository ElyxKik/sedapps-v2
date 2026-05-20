from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    CORE_API_URL: str = "http://core-api:8000"
    INTERNAL_API_TOKEN: str = "change-me-internal-token"

    LLM_PROVIDER: str = "deepseek"
    LLM_MODEL: str = "deepseek-v4-pro"
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_TIMEOUT_S: int = 120
    LLM_MAX_RETRIES: int = 2


settings = Settings()  # type: ignore[call-arg]
