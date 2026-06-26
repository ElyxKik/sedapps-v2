from __future__ import annotations

import json
import uuid
from typing import Any

from app.agents.base import AgentInput, BaseAgent

# Whitelist of section types accepted by web-renderer.
ALLOWED_SECTIONS = {
    "hero.split",
    "hero.center",
    "features.grid",
    "about.split",
    "testimonials.carousel",
    "pricing.table",
    "faq.accordion",
    "cta.banner",
    "form.contact",
    "blog.index",
    "richtext",
    "gallery.grid",
}

# Map copywriter section types -> renderer section types
COPY_TO_RENDERER = {
    "hero": "hero.split",
    "features": "features.grid",
    "about": "about.split",
    "testimonials": "testimonials.carousel",
    "pricing": "pricing.table",
    "faq": "faq.accordion",
    "cta_banner": "cta.banner",
    "contact": "form.contact",
}


class FrontendGeneratorAgent(BaseAgent):
    """
    This agent does NOT call the LLM (deterministic mapping).
    It transforms Copywriter+SEO outputs into a strict PageSchema that the
    Next.js web-renderer can consume safely. We keep an LLM-free path because
    deterministic output here = no risk of XSS / broken UI / hallucinated types.
    """

    name = "frontend_generator"

    async def run(self, inp: AgentInput):  # type: ignore[override]
        from app.agents.base import AgentOutput, TokenUsage  # local import to avoid cycle
        import time

        t0 = time.perf_counter()
        try:
            data = self._build_schema(inp)
            return AgentOutput(
                agent=self.name,
                status="ok",
                data=data,
                tokens=TokenUsage(),
                duration_ms=int((time.perf_counter() - t0) * 1000),
                model="deterministic",
            )
        except Exception as e:  # noqa: BLE001
            return AgentOutput(
                agent=self.name,
                status="failed",
                data={},
                duration_ms=int((time.perf_counter() - t0) * 1000),
                warnings=[f"failed: {e}"],
            )

    def _build_schema(self, inp: AgentInput) -> dict[str, Any]:
        copy = inp.context.get("copywriter", {})
        seo = inp.context.get("seo", {})
        form = inp.context.get("form_builder", {})
        design = inp.context.get("designer", {})

        seo_by_slug = {p["slug"]: p for p in seo.get("per_page", [])}
        form_id = form.get("id", "contact-form")

        pages_out: list[dict[str, Any]] = []
        for p in copy.get("pages", []):
            slug = p.get("slug", "home")
            meta = seo_by_slug.get(slug, {})
            sections = []
            for s in p.get("sections", []):
                raw_type = s.get("type")
                rtype = COPY_TO_RENDERER.get(raw_type) or (
                    raw_type if raw_type in ALLOWED_SECTIONS else None
                )
                if not rtype:
                    continue
                props = {k: v for k, v in s.items() if k != "type"}
                if rtype == "form.contact":
                    props = {**props, "form_id": form_id, "layout": "split"}
                sections.append({"id": str(uuid.uuid4()), "type": rtype, "props": props})

            pages_out.append(
                {
                    "meta": {
                        "slug": slug,
                        "title": meta.get("title") or p.get("title") or slug,
                        "description": meta.get("meta_description") or "",
                        "og": meta.get("og") or {},
                        "schema_org": meta.get("schema_org") or {},
                    },
                    "layout": {"header_id": "default", "footer_id": "default"},
                    "sections": sections,
                }
            )

        return {
            "page_schema": {"pages": pages_out},
            "design_tokens": design,
            "seo": {
                "sitemap": seo.get("sitemap", {}),
                "robots": seo.get("robots", "User-agent: *\nAllow: /"),
            },
            "components_used": sorted({s["type"] for p in pages_out for s in p["sections"]}),
        }

    # Unused but required by BaseAgent contract
    def system_prompt(self, inp: AgentInput) -> str:
        return ""

    def user_prompt(self, inp: AgentInput) -> str:
        return json.dumps(inp.context)
