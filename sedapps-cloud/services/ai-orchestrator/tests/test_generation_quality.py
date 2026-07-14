from __future__ import annotations

import asyncio
import json

import pytest

from app.agents.base import AgentInput
from app.agents.qa import QAAgent
from app.agents.site_planner import SitePlannerAgent
from app.agents.static_page_builder import StaticPageBuilderAgent
from app.workflows.site_generation import _prompt_safe_brief
from app.skills import AGENT_SKILLS, SKILL_CATALOG, compose_system_prompt


def _input(*, brief: dict, page: dict | None = None, context: dict | None = None) -> AgentInput:
    return AgentInput(
        project_id="project",
        job_id="job",
        tenant_id="tenant",
        context=context or {"brief": brief},
        params={"page": page or {}},
    )


def _rich_html() -> str:
    words = " ".join(["contenu professionnel utile pour expliquer clairement notre offre"] * 32)
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Une description utile et précise">
    <title>Accueil</title></head><body><header>Sala</header><main>
    <section id="hero"><h1>Construisez votre avenir</h1><p>{words}</p><img src="https://images.example/hero.jpg" alt="Équipe au travail"></section>
    <section id="services"><h2>Nos services</h2><p>Une expertise complète</p><img src="https://images.example/service.jpg" alt="Présentation du service"></section>
    <section id="contact"><h2>Contact</h2><p>Écrivez-nous à hello@example.com</p><form><input name="email"></form></section>
    </main><footer>Sala</footer></body></html>"""


def test_prompt_safe_brief_removes_nested_data_uris() -> None:
    cleaned = _prompt_safe_brief({"logo": "data:image/png;base64,AAA", "nested": ["ok", "data:image/svg+xml,BBB"]})
    assert cleaned == {
        "logo": "[media uploaded separately]",
        "nested": ["ok", "[media uploaded separately]"],
    }


def test_every_agent_skill_exists_and_prompts_are_role_scoped() -> None:
    assigned = {skill for skills in AGENT_SKILLS.values() for skill in skills}
    assert assigned <= SKILL_CATALOG.keys()

    prompt = compose_system_prompt("designer", "CONTRAT JSON")
    assert "Direction artistique premium" in prompt
    assert "Design system" in prompt
    assert "Ingénierie backend et API" not in prompt
    assert prompt.startswith("CONTRAT JSON")
    assert prompt.endswith("sans en modifier le format.")


def test_site_planner_forces_onboarding_sections_and_navigation() -> None:
    brief = {
        "stack": "onepage",
        "sections": [
            {"type": "hero", "enabled": True, "data": {"headline": "Construisez votre avenir"}},
            {"type": "services", "enabled": True, "data": {"title": "Nos services"}},
            {"type": "contact", "enabled": True, "data": {}},
        ],
    }
    parsed = {
        "pages": [{"id": "home", "title": "Accueil", "path": "index.html", "sections": []}],
        "navigation": [{"label": "Lien cassé", "href": "missing.html"}],
    }

    result = SitePlannerAgent.__new__(SitePlannerAgent).post_process(parsed, _input(brief=brief))

    assert [section["id"] for section in result["pages"][0]["sections"]] == ["hero", "services", "contact"]
    assert result["navigation"] == [{"label": "Accueil", "href": "index.html"}]


def test_static_builder_rejects_wrong_onboarding_section_types() -> None:
    brief = {
        "stack": "onepage",
        "sections": [
            {"type": "hero", "enabled": True, "data": {"headline": "Construisez votre avenir"}},
            {"type": "services", "enabled": True, "data": {"title": "Nos services"}},
            {"type": "contact", "enabled": True, "data": {}},
        ],
    }
    page = {"path": "index.html", "components": ["Header", "Hero", "Gallery", "FAQ", "Footer"]}
    metadata = {
        "path": "index.html",
        "sections": [
            {"id": "hero", "component": "Hero"},
            {"id": "gallery", "component": "Gallery"},
            {"id": "faq", "component": "FAQ"},
        ],
    }
    response = f"```html\n{_rich_html()}\n```\n```json\n{json.dumps(metadata)}\n```"

    with pytest.raises(ValueError, match="section types missing"):
        StaticPageBuilderAgent.__new__(StaticPageBuilderAgent)._parse_dual_block(
            response, _input(brief=brief, page=page)
        )


def test_qa_accepts_rich_page_that_respects_onboarding() -> None:
    brief = {
        "stack": "onepage",
        "business_name": "Sala",
        "contact": {"email": "hello@example.com"},
        "sections": [
            {"type": "hero", "enabled": True, "data": {"headline": "Construisez votre avenir"}},
            {"type": "services", "enabled": True, "data": {"title": "Nos services"}},
            {"type": "contact", "enabled": True, "data": {}},
        ],
    }
    page = {
        "path": "index.html",
        "sections": [{"id": "hero"}, {"id": "services"}, {"id": "contact"}],
    }
    context = {
        "brief": brief,
        "seo": {"sitemap": "ok"},
        "static_site": {
            "files": [{"path": "index.html", "content": _rich_html()}],
            "pages": [page],
            "sections": [
                {"page_path": "index.html", "id": "hero", "component": "Hero"},
                {"page_path": "index.html", "id": "services", "component": "ServicesList"},
                {"page_path": "index.html", "id": "contact", "component": "ContactForm"},
            ],
        },
    }

    output = asyncio.run(QAAgent.__new__(QAAgent).run(_input(brief=brief, context=context)))

    assert output.data["score"] == 100
    assert output.data["onboarding_compliance"]["passed"] is True
