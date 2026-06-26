from __future__ import annotations

import json
import re
import time
from typing import Any

from app.agents.base import AgentInput, AgentOutput, BaseAgent, TokenUsage


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _relative_luminance(r: int, g: int, b: int) -> float:
    def _chan(c: int) -> float:
        cs = c / 255.0
        return cs / 12.92 if cs <= 0.03928 else ((cs + 0.055) / 1.055) ** 2.4
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)


def _contrast_ratio(fg: str, bg: str) -> float:
    r1, g1, b1 = _hex_to_rgb(fg)
    r2, g2, b2 = _hex_to_rgb(bg)
    l1 = _relative_luminance(r1, g1, b1)
    l2 = _relative_luminance(r2, g2, b2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


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

            # ── Richesse du contenu ──────────────────────────────
            # Compter les mots visibles (approximation: strip tags)
            visible_text = re.sub(r"<[^>]+>", " ", html)
            visible_text = re.sub(r"\s+", " ", visible_text).strip()
            word_count = len(visible_text.split()) if visible_text else 0

            if word_count < 300:
                issues.append(
                    {"severity": "high", "code": "thin_content", "page": path, "msg": f"Contenu trop court : {word_count} mots (< 300)"}
                )
            elif word_count < 600:
                issues.append(
                    {"severity": "medium", "code": "short_content", "page": path, "msg": f"Contenu limité : {word_count} mots (< 600)"}
                )

            # Compter les sections (approximation via <section> ou headings h2)
            section_count = len(re.findall(r"<section\b", html, re.IGNORECASE))
            h2_count = len(re.findall(r"<h2\b", html, re.IGNORECASE))
            effective_sections = max(section_count, h2_count)
            if effective_sections < 3:
                issues.append(
                    {"severity": "medium", "code": "few_sections", "page": path, "msg": f"Peu de sections : {effective_sections} (< 3)"}
                )

            # Détecter contenu générique
            generic_phrases = [
                "bienvenue sur notre site",
                "nous offrons des services",
                "qualité au meilleur prix",
                "votre satisfaction notre priorité",
                "des professionnels à votre écoute",
                "lorem",
            ]
            for phrase in generic_phrases:
                if phrase in lower:
                    issues.append(
                        {"severity": "medium", "code": "generic_content", "page": path, "msg": f"Contenu générique détecté : '{phrase}'"}
                    )
                    break

            # Vérifier la présence de preuves sociales
            has_testimonials = "testimonial" in lower or "témoin" in lower or "avis client" in lower
            has_stats = bool(re.search(r"\d+[%+\s]", html)) and ("stat" in lower or "chiffre" in lower or "résultat" in lower)
            if path == "index.html" and not has_testimonials and not has_stats:
                issues.append(
                    {"severity": "low", "code": "no_social_proof", "page": path, "msg": "Pas de preuves sociales (témoignages ou statistiques)"}
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

        # ── Tailwind CDN presence ─────────────────────────────
        for f in html_files:
            path = str(f.get("path", "?"))
            html = str(f.get("content", ""))
            if "cdn.tailwindcss.com" not in html.lower():
                issues.append(
                    {"severity": "medium", "code": "no_tailwind", "page": path, "msg": "Tailwind CDN manquant"}
                )

        # ── Color contrast check from design tokens ───────────
        designer = inp.context.get("designer") or {}
        palette = designer.get("palette") if isinstance(designer.get("palette"), dict) else {}
        text_color = palette.get("text")
        bg_color = palette.get("bg")
        if text_color and bg_color:
            try:
                ratio = _contrast_ratio(text_color, bg_color)
                if ratio < 4.5:
                    issues.append(
                        {"severity": "high", "code": "low_contrast", "msg": f"Contraste text/bg insuffisant : {ratio:.1f}:1 (min 4.5:1)"}
                    )
            except (ValueError, IndexError):
                pass  # invalid hex — skip

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
