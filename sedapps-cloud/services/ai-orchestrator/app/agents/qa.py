from __future__ import annotations

import json
import re
import time
from typing import Any

from app.agents.base import AgentInput, AgentOutput, BaseAgent, TokenUsage


class QAAgent(BaseAgent):
    """
    Audite les fichiers HTML statiques générés + SEO + formulaire.
    Heuristiques déterministes (rapide, fiable) — un appel LLM facultatif peut être
    branché en V1 pour des recommandations qualitatives.
    """

    name = "qa"

    SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    async def run(self, inp: AgentInput) -> AgentOutput:  # type: ignore[override]
        t0 = time.perf_counter()
        issues: list[dict[str, Any]] = []
        auto_fixes: list[str] = []

        static_site = inp.context.get("static_site", {})
        files = static_site.get("generated_files") or static_site.get("files") or []
        html_files = [
            f for f in files
            if isinstance(f, dict) and str(f.get("path", "")).endswith(".html")
        ]
        seo = inp.context.get("seo") or {}

        if not html_files:
            issues.append(
                {"severity": "critical", "code": "no_pages", "msg": "Aucune page générée."}
            )

        known_paths = {str(f.get("path", "")) for f in html_files}
        for f in html_files:
            path = str(f.get("path", "?"))
            html = str(f.get("content", ""))
            lower = html.lower()

            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            title = (title_match.group(1).strip() if title_match else "")
            if not title:
                issues.append(
                    {"severity": "high", "code": "missing_title", "page": path, "msg": "Titre manquant"}
                )
            elif len(title) > 70:
                issues.append(
                    {"severity": "medium", "code": "title_too_long", "page": path, "msg": f"Title {len(title)} chars (>70)"}
                )

            desc_match = re.search(
                r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', html, re.IGNORECASE
            )
            desc = (desc_match.group(1).strip() if desc_match else "")
            if not desc:
                issues.append(
                    {"severity": "medium", "code": "missing_meta_desc", "page": path, "msg": "Meta description manquante"}
                )
            elif len(desc) > 160:
                issues.append(
                    {"severity": "low", "code": "meta_too_long", "page": path, "msg": f"Meta {len(desc)} chars (>160)"}
                )

            if "<h1" not in lower:
                issues.append(
                    {"severity": "high", "code": "no_h1", "page": path, "msg": "Pas de H1"}
                )
            if "<header" not in lower or "<footer" not in lower:
                issues.append(
                    {"severity": "medium", "code": "no_header_footer", "page": path, "msg": "Header ou footer manquant"}
                )
            if "viewport" not in lower:
                issues.append(
                    {"severity": "high", "code": "no_viewport", "page": path, "msg": "Meta viewport manquante (mobile)"}
                )
            if "lorem ipsum" in lower or "placeholder" in lower or "todo" in lower:
                issues.append(
                    {"severity": "high", "code": "placeholder_content", "page": path, "msg": "Contenu placeholder détecté"}
                )
            if path in ("index.html", "contact.html") and "<form" not in lower:
                issues.append(
                    {"severity": "medium", "code": "no_contact_form", "page": path, "msg": "Pas de formulaire de contact"}
                )
            if "<img" in lower:
                imgs_without_alt = len(re.findall(r"<img(?![^>]*\balt=)[^>]*>", html, re.IGNORECASE))
                if imgs_without_alt:
                    issues.append(
                        {"severity": "low", "code": "img_no_alt", "page": path, "msg": f"{imgs_without_alt} image(s) sans alt"}
                    )

            # liens internes cassés vers d'autres pages html du site
            for href in re.findall(r'href=["\'](?:\./)?([a-z0-9_\-]+\.html)["\']', lower):
                if href not in known_paths:
                    issues.append(
                        {"severity": "high", "code": "broken_link", "page": path, "msg": f"Lien interne cassé : {href}"}
                    )

        if html_files and "index.html" not in known_paths:
            issues.append(
                {"severity": "critical", "code": "no_index", "msg": "index.html absent"}
            )

        if not seo.get("sitemap"):
            issues.append({"severity": "low", "code": "no_sitemap", "msg": "Sitemap absent"})

        # score : 100 - pondération par sévérité
        weights = {"critical": 30, "high": 10, "medium": 4, "low": 1}
        score = max(0, 100 - sum(weights.get(i["severity"], 1) for i in issues))
        status = "ok" if score >= 80 else "partial"

        data = {
            "score": score,
            "issues": sorted(issues, key=lambda i: self.SEVERITY_ORDER.get(i["severity"], 9)),
            "auto_fixes_applied": auto_fixes,
        }
        return AgentOutput(
            agent=self.name,
            status=status,
            data=data,
            tokens=TokenUsage(),
            duration_ms=int((time.perf_counter() - t0) * 1000),
            model="deterministic",
        )

    def system_prompt(self, inp: AgentInput) -> str:  # unused
        return ""

    def user_prompt(self, inp: AgentInput) -> str:  # unused
        return json.dumps(inp.context)
