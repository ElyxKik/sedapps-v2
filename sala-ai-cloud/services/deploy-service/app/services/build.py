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


def prepare_static_files_workspace(deployment_id: str, files: list[dict[str, Any]]) -> Path:
    work_root = Path(settings.DEPLOY_WORK_DIR)
    target = work_root / deployment_id
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    for file in files:
        path = str(file.get("path") or "").strip().lstrip("/")
        content = file.get("content")
        if not path or ".." in Path(path).parts:
            continue
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
        output_path = target / path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    if not (target / "index.html").exists():
        raise BuildError("Static deployment payload does not contain index.html")
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


def validate_deployment_dir(out_dir: Path) -> list[str]:
    """Validate a built site directory before upload. Returns list of issues (empty = OK)."""
    issues: list[str] = []

    if not out_dir.exists() or not out_dir.is_dir():
        issues.append("output directory does not exist")
        return issues

    index = out_dir / "index.html"
    if not index.exists():
        issues.append("index.html missing in output")
    else:
        html = index.read_text(encoding="utf-8", errors="replace")
        if "TODO" in html or "FIXME" in html:
            issues.append("TODO/FIXME found in index.html")
        if "lorem ipsum" in html.lower():
            issues.append("placeholder text 'lorem ipsum' in index.html")
        if len(html) < 500:
            issues.append(f"index.html suspiciously small ({len(html)} bytes)")

    # Check for at least one CSS file
    css_files = list(out_dir.rglob("*.css"))
    if not css_files:
        issues.append("no CSS files found in output")

    # Check for broken internal links (href to .html files that don't exist)
    if index.exists():
        import re as _re
        html = index.read_text(encoding="utf-8", errors="replace")
        for match in _re.finditer(r'href=["\']([^"\']+\.html)["\']', html):
            href = match.group(1)
            if href.startswith("http"):
                continue
            target_file = out_dir / href.lstrip("/")
            if not target_file.exists():
                issues.append(f"broken internal link: {href}")

    # Check total size is reasonable (< 50MB)
    total_size = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
    if total_size > 50 * 1024 * 1024:
        issues.append(f"output too large: {total_size // 1024 // 1024}MB")

    return issues


def cleanup_workdir(deployment_id: str) -> None:
    """Remove temporary build directories after deployment."""
    work_root = Path(settings.DEPLOY_WORK_DIR)
    target = work_root / deployment_id
    packages = work_root / f"{deployment_id}-packages"
    for d in (target, packages):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
