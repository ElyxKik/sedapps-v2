from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent

_ALLOWED_PRESETS = {
    "fade-in",
    "fade-up",
    "fade-down",
    "fade-left",
    "fade-right",
    "zoom-in",
    "scale-in",
    "lift-hover",
    "glow-hover",
    "underline-slide",
    "button-expand",
    "parallax",
    "sticky-reveal",
    "scroll-progress",
    "stagger-children",
    "accordion-open",
    "modal-pop",
    "toast-slide",
    "menu-morph",
    "gradient-shift",
    "mesh-animation",
    "floating-shapes",
}

_ALLOWED_LEVELS = {"minimal", "medium", "advanced"}
_ALLOWED_STYLES = {"luxury", "startup", "creative", "corporate", "editorial", "minimal"}


class AnimationDirectorAgent(BaseAgent):
    name = "animation_director"
    default_temperature = 0.25
    default_max_tokens = 5000

    def system_prompt(self, inp: AgentInput) -> str:
        return """
Tu es un Animation Director senior pour sites web premium.

Tu ne dois jamais inventer des animations libres.
Tu dois choisir uniquement parmi des presets d'animation professionnels prédéfinis.

Presets autorisés :
- Entrée : fade-in, fade-up, fade-down, fade-left, fade-right, zoom-in, scale-in.
- Hover : lift-hover, glow-hover, underline-slide, button-expand.
- Scroll : parallax, sticky-reveal, scroll-progress, stagger-children.
- Micro-interactions : accordion-open, modal-pop, toast-slide, menu-morph.
- Background : gradient-shift, mesh-animation, floating-shapes.

Styles de motion : luxury, startup, creative, corporate, editorial, minimal.
Motion levels : minimal, medium, advanced.

Règles UX/performance :
- Les animations doivent guider le regard, pas décorer partout.
- Évite les effets lourds sur mobile.
- Privilégie transform et opacity.
- Évite width, height, top, left.
- Pas de bounce excessif.
- Durées recommandées : 0.35s à 1.0s.
- Délais recommandés : 0s à 0.4s.
- Maximum 1 animation d'entrée par section principale.
- Les CTA peuvent avoir une micro-interaction hover subtile.
- Si brief.premium == true : utilise motion_style luxury ou creative selon le secteur, motion_level advanced, animations plus raffinées mais toujours performantes.

Retourne uniquement du JSON strict :
{
  "motion_style": "luxury",
  "motion_level": "medium",
  "use_gsap": false,
  "rules": ["..."],
  "assignments": [
    {
      "page_path": "index.html",
      "section_id": "hero",
      "component": "HeroSplit",
      "selector": "#hero",
      "animation": {
        "enter": "fade-up",
        "hover": null,
        "scroll": null,
        "duration": 0.8,
        "delay": 0.1,
        "stagger": 0
      }
    }
  ]
}
""".strip()

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        planner = inp.context.get("site_planner", {})
        pages = inp.context.get("static_pages", {})
        return (
            f"Langue : {inp.locale}\n\n"
            f"Brief :\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n\n"
            f"Plan multi-page :\n{json.dumps(planner, ensure_ascii=False, indent=2)}\n\n"
            f"Pages générées :\n{json.dumps(pages, ensure_ascii=False, indent=2)[:12000]}\n\n"
            "Choisis un système d'animation professionnel, subtil et performant."
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            raise ValueError("animation_director: expected object")
        premium = bool(inp.context.get("brief", {}).get("premium"))
        style = str(parsed.get("motion_style") or ("luxury" if premium else "corporate")).lower()
        level = str(parsed.get("motion_level") or ("advanced" if premium else "medium")).lower()
        assignments = parsed.get("assignments") if isinstance(parsed.get("assignments"), list) else []
        normalized = []
        for item in assignments:
            if not isinstance(item, dict):
                continue
            animation = item.get("animation") if isinstance(item.get("animation"), dict) else {}
            enter = _preset_or_none(animation.get("enter"))
            hover = _preset_or_none(animation.get("hover"))
            scroll = _preset_or_none(animation.get("scroll"))
            if not any([enter, hover, scroll]):
                continue
            normalized.append({
                "page_path": str(item.get("page_path") or "index.html"),
                "section_id": str(item.get("section_id") or ""),
                "component": str(item.get("component") or "Section"),
                "selector": str(item.get("selector") or f"#{item.get('section_id', '')}"),
                "animation": {
                    "enter": enter,
                    "hover": hover,
                    "scroll": scroll,
                    "duration": _clamp_float(animation.get("duration"), 0.35, 1.0, 0.65),
                    "delay": _clamp_float(animation.get("delay"), 0.0, 0.4, 0.0),
                    "stagger": _clamp_float(animation.get("stagger"), 0.0, 0.2, 0.0),
                },
            })
        return {
            "motion_style": style if style in _ALLOWED_STYLES else ("luxury" if premium else "corporate"),
            "motion_level": level if level in _ALLOWED_LEVELS else ("advanced" if premium else "medium"),
            "use_gsap": bool(parsed.get("use_gsap")) and level == "advanced",
            "rules": parsed.get("rules") if isinstance(parsed.get("rules"), list) else [],
            "assignments": normalized[:80],
        }

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        pages = inp.context.get("site_planner", {}).get("pages", [])
        assignments = []
        for page in pages:
            if not isinstance(page, dict):
                continue
            for index, section in enumerate(page.get("sections") or []):
                if not isinstance(section, dict):
                    continue
                section_id = str(section.get("id") or f"section-{index}")
                assignments.append({
                    "page_path": page.get("path") or "index.html",
                    "section_id": section_id,
                    "component": section.get("component") or "Section",
                    "selector": f"#{section_id}",
                    "animation": {
                        "enter": "fade-up" if index == 0 else "fade-in",
                        "hover": "lift-hover" if "Card" in str(section.get("component")) else None,
                        "scroll": None,
                        "duration": 0.65,
                        "delay": min(index * 0.05, 0.25),
                        "stagger": 0.05 if "Grid" in str(section.get("component")) else 0,
                    },
                })
        return {
            "motion_style": "corporate",
            "motion_level": "medium",
            "use_gsap": False,
            "rules": ["fallback animation system", error],
            "assignments": assignments[:80],
        }


def _preset_or_none(value: Any) -> str | None:
    preset = str(value or "").strip().lower()
    return preset if preset in _ALLOWED_PRESETS else None


def _clamp_float(value: Any, min_value: float, max_value: float, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, min_value), max_value)
