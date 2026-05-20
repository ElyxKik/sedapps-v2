from __future__ import annotations

import json
import uuid
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class FormBuilderAgent(BaseAgent):
    name = "form_builder"
    default_temperature = 0.2

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es un expert UX formulaires. À partir d'un brief, "
            "génère le schéma d'un formulaire de contact (champs + validation). "
            "Réponds en JSON STRICT :\n"
            "{\n"
            '  "name": "Contact",\n'
            '  "fields": [\n'
            '    {"key":"name","label":"Nom","type":"text","required":true,"max":120},\n'
            '    {"key":"email","label":"Email","type":"email","required":true},\n'
            '    {"key":"phone","label":"Téléphone","type":"tel","required":false},\n'
            '    {"key":"message","label":"Message","type":"textarea","required":true,"max":2000}\n'
            "  ],\n"
            '  "submit_label":"Envoyer",\n'
            '  "success_message":"Merci ! Nous vous recontactons sous 24h.",\n'
            '  "anti_spam": { "honeypot":"website_url", "recaptcha":false }\n'
            "}"
        )

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        return (
            f"Brief :\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n"
            f"Objectifs : {brief.get('objectives', [])}\n"
            f"Locale : {inp.locale}"
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict) or "fields" not in parsed:
            raise ValueError("form_builder: missing 'fields'")
        parsed.setdefault("id", str(uuid.uuid4()))
        return parsed

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "name": "Contact",
            "fields": [
                {"key": "name", "label": "Nom", "type": "text", "required": True, "max": 120},
                {"key": "email", "label": "Email", "type": "email", "required": True},
                {"key": "message", "label": "Message", "type": "textarea",
                 "required": True, "max": 2000},
            ],
            "submit_label": "Envoyer",
            "success_message": "Merci, nous revenons vers vous rapidement.",
            "anti_spam": {"honeypot": "website_url", "recaptcha": False},
        }
