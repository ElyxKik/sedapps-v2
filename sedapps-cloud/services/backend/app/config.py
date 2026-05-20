from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/sedapps"
    supabase_url: str = ""
    supabase_key: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    jwt_secret: str = "change-me-in-production-please"
    jwt_algorithm: str = "HS256"
    access_token_expires_min: int = 60 * 24 * 7  # 7 jours
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    class Config:
        env_file = ".env"
        env_prefix = "SEDAPPS_"
        extra = "ignore"


settings = Settings()
