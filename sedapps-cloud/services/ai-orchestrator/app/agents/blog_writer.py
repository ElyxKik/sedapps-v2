from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class BlogWriterAgent(BaseAgent):
    name = "blog_writer"
    default_temperature = 0.8
    default_max_tokens = 8000
    use_thinking = False  # peut être activé pour des sujets complexes

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es un rédacteur SEO senior. Tu écris des articles de blog longs, "
            "structurés, scannables et optimisés SEO. Format Markdown. "
            "Réponds en JSON STRICT :\n"
            "{\n"
            '  "title":"...",\n'
            '  "slug":"...",\n'
            '  "excerpt":"... (160 chars max)",\n'
            '  "content_md":"# Titre\\n\\n## H2\\n...",\n'
            '  "seo": { "title":"...", "meta_description":"...", "keywords":["..."],\n'
            '            "og_image_url":"", "canonical":"" },\n'
            '  "suggested_tags":["..."],\n'
            '  "cover_image_prompt":"prompt pour générer l\'image (FR)"\n'
            "}"
        )

    def user_prompt(self, inp: AgentInput) -> str:
        p = inp.params
        return (
            f"Sujet : {p.get('topic')}\n"
            f"Mot-clé cible : {p.get('target_keyword')}\n"
            f"Catégorie : {p.get('category')}\n"
            f"Tonalité : {p.get('tone', 'professionnel')}\n"
            f"Longueur visée (mots) : {p.get('length', 800)}\n"
            f"Liens internes (slugs) : {p.get('internal_links', [])}\n"
            f"Locale : {inp.locale}\n\n"
            f"Brief de la marque :\n{json.dumps(inp.context.get('brief', {}), ensure_ascii=False)}"
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        required = {"title", "content_md"}
        if not isinstance(parsed, dict) or not required.issubset(parsed.keys()):
            raise ValueError("blog_writer: missing required keys")
        return parsed
