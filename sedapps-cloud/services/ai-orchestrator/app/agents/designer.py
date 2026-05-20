from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class DesignerAgent(BaseAgent):
    name = "designer"
    default_temperature = 0.4

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es un Senior Brand Designer. Tu produis un SYSTÈME DE DESIGN cohérent "
            "(design tokens) à partir d'un brief de marque. "
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
            '  "vibe": "moderne|chaleureux|premium|minimal|fun|corporate" \n'
            "}\n"
            "Contraintes : couleurs accessibles (contraste >= 4.5 sur text/bg), polices "
            "disponibles sur Google Fonts."
        )

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        return (
            "Génère le design system pour ce projet :\n"
            f"{json.dumps(brief, ensure_ascii=False, indent=2)}\n"
            f"Locale : {inp.locale}."
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        required = {"palette", "typography", "spacing", "radius"}
        if not isinstance(parsed, dict) or not required.issubset(parsed.keys()):
            raise ValueError("designer: missing keys")
        return parsed

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        return {
            "palette": {
                "primary": "#6366F1", "secondary": "#8B5CF6", "accent": "#22D3EE",
                "bg": "#0F1117", "surface": "#161B27", "text": "#F8FAFC", "muted": "#94A3B8",
                "success": "#10B981", "warning": "#F59E0B", "danger": "#EF4444",
            },
            "typography": {
                "heading": "Plus Jakarta Sans", "body": "Inter",
                "scale": {"h1": "2.5rem", "h2": "2rem", "h3": "1.5rem",
                          "body": "1rem", "small": "0.875rem"},
            },
            "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px",
                        "xl": "32px", "2xl": "48px", "3xl": "64px"},
            "radius": {"sm": "6px", "md": "10px", "lg": "16px", "full": "9999px"},
            "shadow": {"sm": "0 1px 2px rgba(0,0,0,.1)",
                       "md": "0 4px 12px rgba(0,0,0,.15)",
                       "lg": "0 16px 48px rgba(0,0,0,.25)"},
            "vibe": "moderne",
        }
