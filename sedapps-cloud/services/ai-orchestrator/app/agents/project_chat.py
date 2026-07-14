from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class ProjectChatAgent(BaseAgent):
    name = "project_chat"
    default_temperature = 0.35
    default_max_tokens = 1200

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es Sala AI, assistant du projet de site. Réponds en français de façon concise "
            "et utile à partir du brief et du Design System fournis. Retourne uniquement un JSON "
            "{\"message\": \"...\"}. N'affirme jamais avoir modifié ou publié le site si aucune "
            "opération explicite n'est fournie."
        )

    def user_prompt(self, inp: AgentInput) -> str:
        return json.dumps(
            {"project": inp.context, "messages": inp.params.get("messages", [])[-20:]},
            ensure_ascii=False,
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        message = parsed.get("message") if isinstance(parsed, dict) else None
        if not isinstance(message, str) or not message.strip():
            raise ValueError("project_chat: message required")
        return {"message": message.strip()}


__all__ = ["ProjectChatAgent"]
