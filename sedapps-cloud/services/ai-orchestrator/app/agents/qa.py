from __future__ import annotations

import json
import re
import time
from html import unescape
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

    @staticmethod
    def _normalized_identifier(value: Any) -> str:
        return re.sub(r"[^a-z0-9]", "", str(value).lower())

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
        brief = inp.context.get("brief", {}) if isinstance(inp.context.get("brief"), dict) else {}
        plan_pages = static_site.get("pages") if isinstance(static_site.get("pages"), list) else []
        requested_pages = brief.get("pages") if isinstance(brief.get("pages"), list) else []
        stack = str(brief.get("stack") or "onepage")
        expected_page_count = 1 if stack == "onepage" else max(len(requested_pages), 3)
        if len(html_files) < expected_page_count:
            issues.append({
                "severity": "critical",
                "code": "onboarding_pages_missing",
                "msg": f"Seulement {len(html_files)}/{expected_page_count} pages demandées ont été générées",
            })

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
            visible_text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
            visible_text = re.sub(r"<[^>]+>", " ", visible_text)
            word_count = len(re.findall(r"\b\w{2,}\b", visible_text, re.UNICODE))
            minimum_words = 100 if "contact" in path else 180
            if word_count < minimum_words:
                issues.append({
                    "severity": "high",
                    "code": "thin_content",
                    "page": path,
                    "msg": f"Contenu trop pauvre : {word_count}/{minimum_words} mots",
                })

            page_plan = next(
                (page for page in plan_pages if isinstance(page, dict) and str(page.get("path")) == path),
                {},
            )
            planned_sections = page_plan.get("sections") if isinstance(page_plan.get("sections"), list) else []
            planned_components = [
                item for item in (page_plan.get("components") or [])
                if str(item).lower() not in {"header", "footer"}
            ]
            onboarding_sections = [
                item for item in (brief.get("sections") or [])
                if isinstance(item, dict) and item.get("enabled", True)
            ]
            expected_sections = len(planned_sections) or len(planned_components)
            if path == "index.html" and stack == "onepage":
                expected_sections = max(expected_sections, len(onboarding_sections))
            expected_sections = max(3, expected_sections)
            actual_sections = len(re.findall(r"<section\b", lower))
            if actual_sections < expected_sections:
                issues.append({
                    "severity": "critical",
                    "code": "onboarding_sections_missing",
                    "page": path,
                    "msg": f"Sections incomplètes : {actual_sections}/{expected_sections}",
                })

            if path == "index.html" and stack == "onepage" and onboarding_sections:
                section_metadata = [
                    section for section in (static_site.get("sections") or [])
                    if isinstance(section, dict) and str(section.get("page_path")) == path
                ]
                metadata_identifiers = {
                    self._normalized_identifier(section.get(key))
                    for section in section_metadata
                    for key in ("id", "component")
                    if section.get(key)
                }
                missing_section_types = []
                for item in onboarding_sections:
                    requested_type = self._normalized_identifier(item.get("type"))
                    if requested_type and not any(
                        requested_type in identifier or identifier in requested_type
                        for identifier in metadata_identifiers
                    ):
                        missing_section_types.append(str(item.get("type")))
                if missing_section_types:
                    issues.append({
                        "severity": "critical",
                        "code": "onboarding_section_types_missing",
                        "page": path,
                        "msg": "Types de sections absents : " + ", ".join(missing_section_types),
                    })

            image_count = len(re.findall(r"<img\b", lower))
            minimum_images = 1 if "contact" in path else 2
            if image_count < minimum_images:
                issues.append({
                    "severity": "high",
                    "code": "missing_visual_content",
                    "page": path,
                    "msg": f"Seulement {image_count}/{minimum_images} images pertinentes",
                })
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

        combined_html = unescape(
            " ".join(str(item.get("content", "")) for item in html_files)
        ).lower()
        required_values = []
        contact = brief.get("contact") if isinstance(brief.get("contact"), dict) else {}
        for value in (contact.get("email"), contact.get("phone"), brief.get("business_name")):
            if isinstance(value, str) and value.strip():
                required_values.append(value.strip())
        for section in (brief.get("sections") or []):
            if not isinstance(section, dict) or not section.get("enabled", True):
                continue
            data = section.get("data") if isinstance(section.get("data"), dict) else {}
            for key in ("headline", "title", "description", "body", "cta_text"):
                value = data.get(key)
                if isinstance(value, str) and len(value.strip()) >= 3:
                    required_values.append(value.strip())
        required_values = list(dict.fromkeys(required_values))
        missing_values = [value for value in required_values if value.lower() not in combined_html]
        if missing_values:
            issues.append({
                "severity": "high",
                "code": "onboarding_values_ignored",
                "msg": "Informations de l’onboarding absentes : " + ", ".join(missing_values),
            })

        # score : 100 - pondération par sévérité
        weights = {"critical": 30, "high": 10, "medium": 4, "low": 1}
        score = max(0, 100 - sum(weights.get(i["severity"], 1) for i in issues))
        status = "ok" if score >= 80 else "partial"

        data = {
            "score": score,
            "issues": sorted(issues, key=lambda i: self.SEVERITY_ORDER.get(i["severity"], 9)),
            "auto_fixes_applied": auto_fixes,
            "onboarding_compliance": {
                "requested_pages": expected_page_count,
                "generated_pages": len(html_files),
                "missing_values": missing_values,
                "passed": not any(str(item.get("code", "")).startswith("onboarding_") for item in issues),
            },
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
