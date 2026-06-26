from __future__ import annotations

import json
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


def _lighten(hex_color: str, amount: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def _darken(hex_color: str, amount: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _is_light(hex_color: str) -> bool:
    r, g, b = _hex_to_rgb(hex_color)
    return _relative_luminance(r, g, b) > 0.5


class DesignerAgent(BaseAgent):
    name = "designer"
    default_temperature = 0.4

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es un Senior Brand Designer. Tu produis un SYSTÈME DE DESIGN cohérent "
            "(design tokens) à partir d'un brief de marque.\n\n"
            "⚠ RÈGLE ABSOLUE : Si le brief contient primary_color, secondary_color ou font_style, "
            "tu DOIS les utiliser comme couleurs principales et police de titre. "
            "Tu ne JAMAIS remplacer les couleurs choisies par l'utilisateur. "
            "Tu peux uniquement compléter avec des couleurs dérivées (bg, surface, text, muted, accent) "
            "qui s'harmonisent avec les couleurs imposées.\n\n"
            "Si le brief contient logo_url, tu DOIS le mentionner dans le champ \"logo_url\".\n\n"
            "Réponds STRICTEMENT en JSON valide (un seul objet), sans texte autour. "
            "Schéma attendu :\n"
            "{\n"
            '  "palette": { "primary": "#hex", "secondary": "#hex", "accent": "#hex",\n'
            '               "bg": "#hex", "surface": "#hex", "text": "#hex", "muted": "#hex",\n'
            '               "success": "#hex", "warning": "#hex", "danger": "#hex" },\n'
            '  "typography": { "heading": "Font Name", "body": "Font Name",\n'
            '                   "scale": { "h1": "rem", "h2": "rem", "h3": "rem", "body": "rem", "small": "rem" } },\n'
            '  "spacing":   { "xs":"4px", "sm":"8px", "md":"16px", "lg":"24px", "xl":"32px", "2xl":"48px", "3xl":"64px" },\n'
            '  "radius":    { "sm":"6px", "md":"10px", "lg":"16px", "full":"9999px" },\n'
            '  "shadow":    { "sm":"...", "md":"...", "lg":"..." },\n'
            '  "vibe": "moderne|chaleureux|premium|minimal|fun|corporate",\n'
            '  "logo_url": "url ou null"\n'
            "}\n"
            "Contraintes : couleurs accessibles (contraste >= 4.5 sur text/bg), polices "
            "disponibles sur Google Fonts."
        )

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        primary = brief.get("primary_color") or brief.get("brand", {}).get("primary_color")
        secondary = brief.get("secondary_color") or brief.get("brand", {}).get("secondary_color")
        font = brief.get("font_style") or brief.get("font_pref") or brief.get("brand", {}).get("font_heading")
        logo = brief.get("logo_url") or brief.get("identity", {}).get("logo_url")
        style_kw = brief.get("style_keywords") or brief.get("brand", {}).get("style_keywords") or []
        tone = brief.get("tone") or brief.get("brand", {}).get("tone")

        constraints = []
        if primary:
            constraints.append(f"⚠ COULEUR PRIMAIRE IMPOSÉE : {primary} — tu DOIS l'utiliser pour palette.primary.")
        if secondary:
            constraints.append(f"⚠ COULEUR SECONDAIRE IMPOSÉE : {secondary} — tu DOIS l'utiliser pour palette.secondary.")
        if font:
            constraints.append(f"⚠ POLICE TITRES IMPOSÉE : {font} — tu DOIS l'utiliser pour typography.heading.")
        if logo:
            constraints.append(f"⚠ LOGO FOURNI : {logo} — inclus-le dans logo_url.")
        if style_kw:
            constraints.append(f"Style keywords : {', '.join(style_kw)}.")
        if tone:
            constraints.append(f"Ton de marque : {tone}.")

        constraints_str = "\n".join(constraints) if constraints else "Aucune contrainte spécifique — sois créatif."

        return (
            "Génère le design system pour ce projet :\n"
            f"{json.dumps(brief, ensure_ascii=False, indent=2)}\n\n"
            f"CONTRAINTES OBLIGATOIRES :\n{constraints_str}\n\n"
            f"Locale : {inp.locale}."
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        required = {"palette", "typography", "spacing", "radius"}
        if not isinstance(parsed, dict) or not required.issubset(parsed.keys()):
            raise ValueError("designer: missing keys")

        brief = inp.context.get("brief", {})
        palette = parsed.get("palette") if isinstance(parsed.get("palette"), dict) else {}
        typo = parsed.get("typography") if isinstance(parsed.get("typography"), dict) else {}

        # Enforce user's onboarding choices — override LLM output
        primary = brief.get("primary_color") or brief.get("brand", {}).get("primary_color")
        secondary = brief.get("secondary_color") or brief.get("brand", {}).get("secondary_color")
        font = brief.get("font_style") or brief.get("font_pref") or brief.get("brand", {}).get("font_heading")
        logo = brief.get("logo_url") or brief.get("identity", {}).get("logo_url")

        if primary:
            palette["primary"] = primary
        if secondary:
            palette["secondary"] = secondary
        if font:
            typo["heading"] = font
            if not typo.get("body") or typo["body"] == typo.get("heading"):
                typo["body"] = font
        if logo:
            parsed["logo_url"] = logo

        parsed["palette"] = palette
        parsed["typography"] = typo
        return parsed

    def _deterministic_design(self, brief: dict[str, Any]) -> dict[str, Any]:
        """Build design tokens algorithmically when user provides all key constraints."""
        primary = brief.get("primary_color") or brief.get("brand", {}).get("primary_color")
        secondary = brief.get("secondary_color") or brief.get("brand", {}).get("secondary_color")
        font = brief.get("font_style") or brief.get("font_pref") or brief.get("brand", {}).get("font_heading")
        logo = brief.get("logo_url") or brief.get("identity", {}).get("logo_url")

        # Derive supporting colors from the user's primary
        is_light_primary = _is_light(primary)
        bg = "#0F1117" if not is_light_primary else "#F8FAFC"
        surface = "#161B27" if not is_light_primary else "#FFFFFF"
        text_color = "#F8FAFC" if not is_light_primary else "#0F172A"
        muted = "#94A3B8" if not is_light_primary else "#64748B"
        accent = _lighten(primary, 0.3) if not is_light_primary else _darken(primary, 0.2)

        # Ensure contrast
        if _contrast_ratio(text_color, bg) < 4.5:
            text_color = "#FFFFFF" if not is_light_primary else "#000000"

        style_kw = brief.get("style_keywords") or brief.get("brand", {}).get("style_keywords") or []
        vibe = "moderne"
        if style_kw:
            kw_lower = [k.lower() for k in style_kw]
            if any(w in kw_lower for w in ("luxe", "premium", "high-end")):
                vibe = "premium"
            elif any(w in kw_lower for w in ("fun", "playful", "coloré")):
                vibe = "fun"
            elif any(w in kw_lower for w in ("minim", "clean", "épuré")):
                vibe = "minimal"
            elif any(w in kw_lower for w in ("corporate", "professionnel", "sérieux")):
                vibe = "corporate"

        return {
            "palette": {
                "primary": primary,
                "secondary": secondary,
                "accent": accent,
                "bg": bg,
                "surface": surface,
                "text": text_color,
                "muted": muted,
                "success": "#10B981",
                "warning": "#F59E0B",
                "danger": "#EF4444",
            },
            "typography": {
                "heading": font,
                "body": font,
                "scale": {
                    "h1": "2.5rem",
                    "h2": "2rem",
                    "h3": "1.5rem",
                    "body": "1rem",
                    "small": "0.875rem",
                },
            },
            "spacing": {
                "xs": "4px", "sm": "8px", "md": "16px", "lg": "24px",
                "xl": "32px", "2xl": "48px", "3xl": "64px",
            },
            "radius": {"sm": "6px", "md": "10px", "lg": "16px", "full": "9999px"},
            "shadow": {
                "sm": "0 1px 2px rgba(0,0,0,.1)",
                "md": "0 4px 12px rgba(0,0,0,.15)",
                "lg": "0 16px 48px rgba(0,0,0,.25)",
            },
            "vibe": vibe,
            "logo_url": logo,
        }

    async def run(self, inp: AgentInput) -> AgentOutput:  # type: ignore[override]
        """Fast-path: if user provided primary_color, secondary_color and font_style,
        derive design tokens deterministically without calling the LLM."""
        brief = inp.context.get("brief", {})
        primary = brief.get("primary_color") or brief.get("brand", {}).get("primary_color")
        secondary = brief.get("secondary_color") or brief.get("brand", {}).get("secondary_color")
        font = brief.get("font_style") or brief.get("font_pref") or brief.get("brand", {}).get("font_heading")

        if primary and secondary and font:
            t0 = time.perf_counter()
            data = self._deterministic_design(brief)
            return AgentOutput(
                agent=self.name,
                status="ok",
                data=data,
                tokens=TokenUsage(prompt=0, completion=0),
                duration_ms=int((time.perf_counter() - t0) * 1000),
                model="deterministic",
                warnings=["deterministic fast-path: skipped LLM"],
            )

        # Fall back to normal LLM-based generation
        return await super().run(inp)

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        brief = inp.context.get("brief", {})
        primary = brief.get("primary_color") or brief.get("brand", {}).get("primary_color") or "#6366F1"
        secondary = brief.get("secondary_color") or brief.get("brand", {}).get("secondary_color") or "#8B5CF6"
        font = brief.get("font_style") or brief.get("font_pref") or brief.get("brand", {}).get("font_heading") or "Inter"
        logo = brief.get("logo_url") or brief.get("identity", {}).get("logo_url")

        return {
            "palette": {
                "primary": primary,
                "secondary": secondary,
                "accent": "#22D3EE",
                "bg": "#0F1117",
                "surface": "#161B27",
                "text": "#F8FAFC",
                "muted": "#94A3B8",
                "success": "#10B981",
                "warning": "#F59E0B",
                "danger": "#EF4444",
            },
            "typography": {
                "heading": font,
                "body": font,
                "scale": {
                    "h1": "2.5rem",
                    "h2": "2rem",
                    "h3": "1.5rem",
                    "body": "1rem",
                    "small": "0.875rem",
                },
            },
            "spacing": {
                "xs": "4px",
                "sm": "8px",
                "md": "16px",
                "lg": "24px",
                "xl": "32px",
                "2xl": "48px",
                "3xl": "64px",
            },
            "radius": {"sm": "6px", "md": "10px", "lg": "16px", "full": "9999px"},
            "shadow": {
                "sm": "0 1px 2px rgba(0,0,0,.1)",
                "md": "0 4px 12px rgba(0,0,0,.15)",
                "lg": "0 16px 48px rgba(0,0,0,.25)",
            },
            "vibe": "moderne",
            "logo_url": logo,
        }
