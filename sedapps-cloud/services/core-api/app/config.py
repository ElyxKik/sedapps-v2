from pydantic import model_validator
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
    DEPLOY_BASE_DOMAIN: str = "salaai.site"
    INTERNAL_API_TOKEN: str = "change-me-internal-token"

    # OVH Domain purchasing API credentials
    OVH_APP_KEY: str = ""
    OVH_APP_SECRET: str = ""
    OVH_CONSUMER_KEY: str = ""
    OVH_ENDPOINT: str = "ovh-eu"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        if self.APP_ENV.lower() == "production":
            return None
        return r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    @model_validator(mode="after")
    def require_production_secrets(self) -> "Settings":
        if self.APP_ENV.lower() != "production":
            return self
        unsafe_values = {"", "change-me-internal-token", "change-me-in-production-please"}
        if self.JWT_SECRET in unsafe_values:
            raise ValueError("JWT_SECRET must be configured securely in production")
        if self.INTERNAL_API_TOKEN in unsafe_values:
            raise ValueError("INTERNAL_API_TOKEN must be configured securely in production")
        if not self.cors_origins_list:
            raise ValueError("CORS_ORIGINS must contain the Firebase Hosting origin in production")
        return self


settings = Settings()  # type: ignore[call-arg]
