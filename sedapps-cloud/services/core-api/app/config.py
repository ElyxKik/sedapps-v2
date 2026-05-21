from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 30

    CORS_ORIGINS: str = ""

    AI_ORCHESTRATOR_URL: str = "http://ai-orchestrator:8001"
    DEPLOY_SERVICE_URL: str = "http://deploy-service:8002"
    INTERNAL_API_TOKEN: str = "change-me-internal-token"

    # OVH Domain purchasing API credentials
    OVH_APP_KEY: str = ""
    OVH_APP_SECRET: str = ""
    OVH_CONSUMER_KEY: str = ""
    OVH_ENDPOINT: str = "ovh-eu"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()  # type: ignore[call-arg]
