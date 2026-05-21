from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.config import settings


class BuildError(RuntimeError):
    pass


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env={**os.environ, **(env or {})},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode != 0:
        raise BuildError(f"Command failed ({' '.join(cmd)}):\n{proc.stdout[-4000:]}")


def prepare_workspace(deployment_id: str, payload: dict[str, Any], site_url: str) -> Path:
    work_root = Path(settings.DEPLOY_WORK_DIR)
    target = work_root / deployment_id
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    source = settings.WEB_RENDERER_SOURCE
    ignore = shutil.ignore_patterns("node_modules", ".next", "out")
    shutil.copytree(source, target, ignore=ignore)

    packages_dir = target.parent / f"{deployment_id}-packages" / "page-schema"
    if packages_dir.exists():
        shutil.rmtree(packages_dir)
    packages_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(settings.PAGE_SCHEMA_SOURCE, packages_dir, ignore=shutil.ignore_patterns("node_modules", "dist"))

    content_dir = target / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    (content_dir / "site.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return target


def build_static_site(workdir: Path, site_url: str) -> Path:
    env = {
        "NEXT_PUBLIC_SITE_URL": site_url,
        "NEXT_PUBLIC_INBOX_URL": settings.NEXT_PUBLIC_INBOX_URL,
        "NEXT_PUBLIC_ANALYTICS_URL": settings.NEXT_PUBLIC_ANALYTICS_URL,
        "CI": "1",
    }
    _run(["npm", "install"], cwd=workdir, env=env)
    _run(["npm", "run", "build"], cwd=workdir, env=env)
    out = workdir / "out"
    if not out.exists():
        raise BuildError("Next.js build succeeded but `out/` was not created")
    return out
