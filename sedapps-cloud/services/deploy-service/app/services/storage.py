from __future__ import annotations

import mimetypes
from pathlib import Path

import boto3
from botocore.client import Config

from app.config import settings


CACHE_CONTROL_STATIC = "public, max-age=31536000, immutable"
CACHE_CONTROL_HTML = "public, max-age=60, stale-while-revalidate=86400"


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.OVH_S3_ENDPOINT or None,
        region_name=settings.OVH_S3_REGION,
        aws_access_key_id=settings.OVH_S3_ACCESS_KEY or None,
        aws_secret_access_key=settings.OVH_S3_SECRET_KEY or None,
        config=Config(signature_version="s3v4"),
    )


def upload_directory(out_dir: Path, prefix: str) -> dict[str, int | str]:
    files = [p for p in out_dir.rglob("*") if p.is_file()]
    if settings.DEPLOY_DRY_RUN:
        return {"uploaded": len(files), "prefix": prefix, "dry_run": 1}

    if not settings.OVH_S3_BUCKET:
        raise RuntimeError("OVH_S3_BUCKET is required when DEPLOY_DRY_RUN=false")

    s3 = _client()
    uploaded = 0
    for file_path in files:
        rel = file_path.relative_to(out_dir).as_posix()
        key = f"{prefix.rstrip('/')}/{rel}"
        ctype = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        cache_control = CACHE_CONTROL_HTML if rel.endswith(".html") else CACHE_CONTROL_STATIC
        s3.upload_file(
            str(file_path),
            settings.OVH_S3_BUCKET,
            key,
            ExtraArgs={"ContentType": ctype, "CacheControl": cache_control},
        )
        uploaded += 1
    return {"uploaded": uploaded, "prefix": prefix, "dry_run": 0}


def public_url(prefix: str, domain: str) -> str:
    if settings.OVH_S3_PUBLIC_BASE_URL:
        return f"{settings.OVH_S3_PUBLIC_BASE_URL.rstrip('/')}/{prefix.rstrip('/')}/"
    return f"https://{domain}/"
