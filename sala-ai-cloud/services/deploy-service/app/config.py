from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    INTERNAL_API_TOKEN: str

    CORE_API_URL: str = "http://core-api:8000"
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    DEPLOY_DRY_RUN: bool = True
    DEPLOY_BASE_DOMAIN: str = "sedapps.cloud"
    DEPLOY_PUBLIC_BASE_URL: str = "https://sedapps.cloud"
    DEPLOY_WORK_DIR: str = "/tmp/sedapps-deploys"
    WEB_RENDERER_SOURCE: str = Field(default="/workspace/apps/web-renderer")
    ASTRO_RENDERER_SOURCE: str = Field(default="/workspace/apps/astro-renderer")
    PAGE_SCHEMA_SOURCE: str = Field(default="/workspace/packages/page-schema")
    DEFAULT_RENDERER: str = "next"  # "next" | "astro"

    NEXT_PUBLIC_INBOX_URL: str = ""
    NEXT_PUBLIC_ANALYTICS_URL: str = ""

    OVH_ENDPOINT: str = "ovh-eu"
    OVH_APP_KEY: str = ""
    OVH_APP_SECRET: str = ""
    OVH_CONSUMER_KEY: str = ""
    OVH_ZONE_NAME: str = "sedapps.cloud"

    OVH_S3_ENDPOINT: str = ""
    OVH_S3_REGION: str = "gra"
    OVH_S3_BUCKET: str = ""
    OVH_S3_ACCESS_KEY: str = ""
    OVH_S3_SECRET_KEY: str = ""
    OVH_S3_PUBLIC_BASE_URL: str = ""


settings = Settings()
