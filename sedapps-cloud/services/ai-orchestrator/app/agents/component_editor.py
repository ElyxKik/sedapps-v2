from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class ComponentEditorAgent(BaseAgent):
    name = "component_editor"
    default_temperature = 0.15
    default_max_tokens = 1200

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es l'éditeur structuré Sala AI. Tu modifies uniquement le composant fourni. "
            "Retourne un objet JSON {\"ops\": [...], \"message\": \"...\"}. "
            "Opérations autorisées: set_text(value), set_prop(path,value), "
            "unset_prop(path), set_style_token(path,token). Les styles doivent référencer "
            "un token theme.* présent dans le contexte. Aucun HTML, CSS libre, JavaScript, "
            "nouveau composant ou modification hors du component_id sélectionné."
        )

    def user_prompt(self, inp: AgentInput) -> str:
        return json.dumps(
            {
                "instruction": inp.params.get("instruction"),
                "ai_context": inp.context,
            },
            ensure_ascii=False,
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict) or not isinstance(parsed.get("ops"), list):
            raise ValueError("component_editor: ops array required")
        allowed = {"set_text", "set_prop", "unset_prop", "set_style_token"}
        if any(not isinstance(op, dict) or op.get("op") not in allowed for op in parsed["ops"]):
            raise ValueError("component_editor: unsupported operation")
        return {
            "ops": parsed["ops"][:20],
            "message": str(parsed.get("message") or "Modification appliquée."),
        }


__all__ = ["ComponentEditorAgent"]
