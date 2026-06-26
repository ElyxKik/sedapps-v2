from __future__ import annotations

from datetime import datetime
from typing import Any


def generate_site_payload(brief: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    business = brief.get("business_name") or "Mon Site"
    sector = brief.get("sector") or "Services"
    description = brief.get("brief") or f"Site moderne pour {business}"

    agents = [
        {
            "id": "agent-designer",
            "name": "designer",
            "status": "ok",
            "model": "mock-designer-v1",
            "prompt_version": 1,
            "duration_ms": 850,
            "tokens_in": 320,
            "tokens_out": 520,
            "input": {"business_name": business, "sector": sector},
            "output": {"primary": "#0EA5E9", "layout": "modern_sky_blue"},
            "warnings": [],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "agent-copywriter",
            "name": "copywriter",
            "status": "ok",
            "model": "mock-copywriter-v1",
            "prompt_version": 1,
            "duration_ms": 720,
            "tokens_in": 280,
            "tokens_out": 680,
            "input": {"brief": description},
            "output": {"hero_title": f"{business}, votre présence web professionnelle"},
            "warnings": [],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "agent-seo",
            "name": "seo_specialist",
            "status": "ok",
            "model": "mock-seo-v1",
            "prompt_version": 1,
            "duration_ms": 610,
            "tokens_in": 210,
            "tokens_out": 430,
            "input": {"sector": sector},
            "output": {"meta_title": f"{business} | {sector}", "keywords": [sector, business, "site web"]},
            "warnings": [],
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "agent-frontend",
            "name": "frontend_developer",
            "status": "ok",
            "model": "mock-frontend-v1",
            "prompt_version": 1,
            "duration_ms": 980,
            "tokens_in": 400,
            "tokens_out": 900,
            "input": {"sections": ["hero", "services", "faq", "contact"]},
            "output": {"components": ["Header", "Hero", "Cards", "ContactForm"], "responsive": True},
            "warnings": [],
            "created_at": datetime.utcnow().isoformat(),
        },
    ]

    design_tokens = {
        "primary": "#0EA5E9",
        "secondary": "#38BDF8",
        "background": "#F8FAFC",
        "font_heading": "Inter",
    }

    sections = [
        {"id": "hero", "title": "Accueil", "content": f"{business}, votre présence web professionnelle.", "enabled": True},
        {"id": "services", "title": "Services", "content": f"Des solutions adaptées au secteur {sector}.", "enabled": True},
        {"id": "about", "title": "À propos", "content": description, "enabled": True},
        {"id": "contact", "title": "Contact", "content": "Contactez-nous pour démarrer votre projet.", "enabled": True},
    ]

    output = {
        "site_schema": {"pages": 1, "sections": len(sections), "sections_data": sections},
        "design_tokens": design_tokens,
        "seo": {"title": f"{business} | {sector}", "description": description[:155]},
    }
    return agents, output, sections
