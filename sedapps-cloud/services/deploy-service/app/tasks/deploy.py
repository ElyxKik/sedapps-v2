from __future__ import annotations

import logging
from typing import Any

from app.celery_app import celery
from app.config import settings
from app.services.build import build_static_site, prepare_workspace
from app.services.core_client import CoreApiClient
from app.services.ovh_dns import OvhDnsClient
from app.services.storage import public_url, upload_directory

log = logging.getLogger(__name__)


def _domain_for(slug: str, custom_domain: str | None) -> str:
    return custom_domain or f"{slug}.{settings.DEPLOY_BASE_DOMAIN}"


def _s3_prefix(tenant_id: str, project_id: str, site_version_id: str) -> str:
    return f"tenants/{tenant_id}/projects/{project_id}/versions/{site_version_id}"


@celery.task(name="deployments.site", bind=True, max_retries=1)
def deploy_site(self, body: dict[str, Any]) -> dict[str, Any]:
    deployment_id = body["deployment_id"]
    tenant_id = body["tenant_id"]
    project_id = body["project_id"]
    site_version_id = body["site_version_id"]
    slug = body["slug"]
    custom_domain = body.get("custom_domain")
    payload = body["payload"]

    core = CoreApiClient()
    domain = _domain_for(slug, custom_domain)
    site_url = f"https://{domain}"
    prefix = _s3_prefix(tenant_id, project_id, site_version_id)

    core.deployment_update(deployment_id, {"status": "building", "domain": domain})
    try:
        log.info("deployment %s prepare workspace (next/static)", deployment_id)
        workdir = prepare_workspace(deployment_id, payload, site_url)

        log.info("deployment %s build static site", deployment_id)
        out_dir = build_static_site(workdir, site_url)

        core.deployment_update(deployment_id, {"status": "uploading", "domain": domain})
        upload = upload_directory(out_dir, prefix)

        dns_result: dict[str, Any] | None = None
        if not custom_domain:
            target = settings.OVH_S3_PUBLIC_BASE_URL.replace("https://", "").replace("http://", "")
            target = target.split("/")[0] if target else settings.OVH_S3_ENDPOINT.replace("https://", "")
            dns_result = OvhDnsClient().upsert_cname(slug, target)

        url = public_url(prefix, domain)
        result = {
            "status": "success",
            "domain": domain,
            "url": url,
            "prefix": prefix,
            "upload": upload,
            "dns": dns_result,
            "dry_run": settings.DEPLOY_DRY_RUN,
        }
        core.deployment_update(deployment_id, result)
        return result
    except Exception as exc:  # noqa: BLE001
        log.exception("deployment failed")
        core.deployment_update(deployment_id, {"status": "failed", "error": str(exc)[:1900]})
        raise
