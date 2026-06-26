from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/sedapps"
    supabase_url: str = ""
    supabase_key: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    jwt_secret: str = "change-me-in-production-please"
    jwt_algorithm: str = "HS256"
    access_token_expires_min: int = 60 * 24 * 7  # 7 jours
    admin_secret: str = ""
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    # Service URLs
    core_api_url: str = "http://localhost:8000"
    ai_orchestrator_url: str = "http://localhost:8001"
    deploy_service_url: str = "http://localhost:8002"
    inbox_service_url: str = "http://localhost:8003"
    analytics_service_url: str = "http://localhost:8004"
    internal_api_token: str = "change-me-internal-token"

    # Deploy
    deploy_dry_run: bool = True
    deploy_base_domain: str = "sedapps.cloud"
    deploy_public_base_url: str = "https://sedapps.cloud"
    deploy_work_dir: str = "/tmp/sedapps-deploys"
    web_renderer_source: str = ""
    page_schema_source: str = ""

    # OVH
    ovh_endpoint: str = "ovh-eu"
    ovh_app_key: str = ""
    ovh_app_secret: str = ""
    ovh_consumer_key: str = ""
    ovh_zone_name: str = ""
    ovh_s3_endpoint: str = ""
    ovh_s3_region: str = ""
    ovh_s3_bucket: str = ""
    ovh_s3_access_key: str = ""
    ovh_s3_secret_key: str = ""
    ovh_s3_public_base_url: str = ""

    # Inbox / Analytics
    inbox_allowed_origins: str = "*"
    inbox_honeypot_field: str = "website_url"
    inbox_max_field_length: int = 5000
    analytics_respect_dnt: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
