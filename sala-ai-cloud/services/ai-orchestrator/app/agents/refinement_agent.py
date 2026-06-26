from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

from app.agents.base import AgentInput, AgentOutput, BaseAgent, TokenUsage
from app.llm.deepseek import LLMError

log = logging.getLogger(__name__)

_FILE_BLOCK_RE = re.compile(
    r"###\s*FILE:\s*([^\n]+)\n```html\s*([\s\S]*?)```",
    re.IGNORECASE,
)
_CHANGES_FENCE_RE = re.compile(r"```json\s*([\s\S]*?)```", re.IGNORECASE)


class RefinementAgent(BaseAgent):
    name = "refinement_agent"
    default_temperature = 0.35
    # Augmenté pour traiter un fichier HTML complet (12 000–20 000 chars) + génération
    default_max_tokens = 24000

    def system_prompt(self, inp: AgentInput) -> str:  # type: ignore[override]
        """Système prompt pour raffiner UN seul fichier HTML."""
        site = inp.context.get("static_site", {})
        files = site.get("generated_files") or site.get("files") or []
        html_files = [f for f in files if isinstance(f, dict) and str(f.get("path", "")).endswith(".html")]
        file_list = ", ".join(str(f.get("path")) for f in html_files) or "index.html"
        return f"""
Tu es un senior frontend refinement engineer pour sites premium 10K+.

Tu reçois UN fichier HTML statique et un audit QA. Tu dois améliorer ce fichier sans changer son architecture globale.

Objectifs : rendre le site moins template, plus premium, plus convaincant, avec meilleures preuves sociales, CTA percutants, icônes SVG inline, microcopy soignée et détails visuels haut de gamme.

Contraintes :
- Conserve les chemins de fichiers existants : {file_list}
- Ne casse pas les liens CSS/JS existants (./styles.css, ./script.js, cdn.tailwindcss.com).
- Pas d'emojis sauf demande explicite dans le brief.
- N'ajoute aucune dépendance externe supplémentaire.
- Retourne le fichier HTML COMPLET, pas juste les parties modifiées.
- Retourne TOUJOURS le fichier même si peu modifié.

FORMAT DE RÉPONSE OBLIGATOIRE :

### FILE: index.html
```html
<!doctype html>
...tout le HTML amélioré...
```

Puis un bloc JSON avec le résumé des changements :
```json
{{"changes": ["Description du changement 1", "Description du changement 2"]}}
```
""".strip()

    def _make_single_file_prompt(
        self,
        file: dict[str, Any],
        brief: dict[str, Any],
        qa: dict[str, Any],
        strategy: dict[str, Any],
    ) -> str:
        """Construit le user_prompt pour raffiner un seul fichier HTML."""
        path = file.get("path", "")
        # Passe le HTML COMPLET — sans troncature
        html_content = str(file.get("content", ""))

        parts = [
            f"Brief :\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n",
            f"Audit QA :\n{json.dumps(qa, ensure_ascii=False, indent=2)}\n",
        ]
        if strategy:
            strategy_summary = {
                k: strategy.get(k)
                for k in ("positioning", "usp", "emotional_angle", "tone_of_voice")
                if strategy.get(k)
            }
            if strategy_summary:
                parts.append(f"Stratégie de marque :\n{json.dumps(strategy_summary, ensure_ascii=False, indent=2)}\n")

        parts.append(f"Fichier à raffiner :\n\n### FILE: {path}\n```html\n{html_content}\n```")
        return "\n".join(parts)

    def user_prompt(self, inp: AgentInput) -> str:
        """Fallback pour la compatibilité BaseAgent — non utilisé dans le run() custom."""
        site = inp.context.get("static_site", {})
        files = site.get("generated_files") or site.get("files") or []
        html_files = [f for f in files if isinstance(f, dict) and str(f.get("path", "")).endswith(".html")]
        qa = inp.context.get("qa") or inp.context.get("premium_qa") or {}
        brief = inp.context.get("brief", {})
        strategy = inp.context.get("strategy_director", {})
        if html_files:
            return self._make_single_file_prompt(html_files[0], brief, qa, strategy)
        return "Aucun fichier HTML à raffiner."

    async def _refine_single_file(
        self,
        file: dict[str, Any],
        inp: AgentInput,
        t0: float,
    ) -> tuple[dict[str, Any], int, int, list[str]]:
        """
        Raffine un seul fichier HTML via un appel LLM dédié.
        Retourne (file_result, tokens_in, tokens_out, changes).
        """
        brief = inp.context.get("brief", {})
        qa = inp.context.get("qa") or inp.context.get("premium_qa") or {}
        strategy = inp.context.get("strategy_director", {})

        messages = [
            {"role": "system", "content": self.system_prompt(inp)},
            {"role": "user", "content": self._make_single_file_prompt(file, brief, qa, strategy)},
        ]
        tokens_in = tokens_out = 0
        max_retries = 1
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                resp = await self.client.chat(
                    messages=messages,
                    temperature=self.default_temperature,
                    max_tokens=self.default_max_tokens,
                    thinking=False,
                    response_format_json=False,
                )
                tokens_in += resp.usage.prompt_tokens
                tokens_out += resp.usage.completion_tokens

                try:
                    data = self._parse_single_block(resp.content, file)
                    return data, tokens_in, tokens_out, data.pop("_changes", [])
                except (ValueError, KeyError) as parse_err:
                    last_error = parse_err
                    if attempt < max_retries:
                        messages.append({"role": "assistant", "content": resp.content})
                        messages.append({
                            "role": "user",
                            "content": (
                                f"Erreur : {parse_err}\n\n"
                                "Utilise le format ### FILE: chemin.html suivi de ```html ... ``` pour le fichier complet. "
                                "Ne mets JAMAIS le HTML dans du JSON. Retourne le fichier HTML ENTIER."
                            ),
                        })
                        continue
                    raise parse_err

            except (LLMError, ValueError, KeyError) as e:
                last_error = e
                if attempt == max_retries:
                    break

        # Fallback : retourner le fichier original non modifié
        log.warning(
            "refinement_agent: failed to refine %s, keeping original. Error: %s",
            file.get("path"),
            last_error,
        )
        return {"path": file.get("path", ""), "content": file.get("content", "")}, tokens_in, tokens_out, []

    async def run(self, inp: AgentInput) -> AgentOutput:  # type: ignore[override]
        """
        Traite chaque fichier HTML dans un appel LLM séparé pour éviter la troncature.
        Les fichiers non-HTML (styles.css, script.js) sont conservés à l'identique.
        """
        t0 = time.perf_counter()
        site = inp.context.get("static_site", {})
        all_files = site.get("generated_files") or site.get("files") or []
        if not isinstance(all_files, list) or not all_files:
            log.warning("refinement_agent: no files to refine")
            return AgentOutput(
                agent=self.name,
                status="partial",
                data={"files": [], "changes": ["no files to refine"]},
                tokens=TokenUsage(prompt=0, completion=0),
                duration_ms=int((time.perf_counter() - t0) * 1000),
                warnings=["no files to refine"],
            )

        html_files = [f for f in all_files if isinstance(f, dict) and str(f.get("path", "")).endswith(".html")]
        non_html_files = [f for f in all_files if isinstance(f, dict) and not str(f.get("path", "")).endswith(".html")]

        total_in = total_out = 0
        all_changes: list[str] = []
        refined_html: list[dict[str, Any]] = []

        # Parallel refinement — all HTML files refined concurrently
        tasks = [self._refine_single_file(file, inp, t0) for file in html_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                log.error("refinement_agent: crashed for %s: %s", html_files[i].get("path"), result)
                refined_html.append({"path": html_files[i].get("path", ""), "content": html_files[i].get("content", "")})
                continue
            file_result, t_in, t_out, changes = result
            total_in += t_in
            total_out += t_out
            all_changes.extend(changes)
            refined_html.append(file_result)

        final_files = refined_html + non_html_files

        return AgentOutput(
            agent=self.name,
            status="ok",
            data={"files": final_files, "changes": all_changes},
            tokens=TokenUsage(prompt=total_in, completion=total_out),
            duration_ms=int((time.perf_counter() - t0) * 1000),
            warnings=[],
        )

    def _parse_single_block(self, text: str, original_file: dict[str, Any]) -> dict[str, Any]:
        """Parse la réponse LLM pour un seul fichier."""
        matches = _FILE_BLOCK_RE.findall(text)

        if matches:
            path_raw, html_raw = matches[0]
            path = str(path_raw).strip().lstrip("/")
            html = html_raw.strip()
        else:
            # Fallback : chercher un bloc ```html nu
            html_match = re.search(r"```html\s*([\s\S]*?)```", text, re.IGNORECASE)
            if html_match:
                html = html_match.group(1).strip()
                path = str(original_file.get("path", "index.html"))
            else:
                raise ValueError(f"refinement_agent: no ```html block found in response for {original_file.get('path')}")

        if not html or "<!doctype" not in html.lower():
            raise ValueError(f"refinement_agent: invalid HTML for {original_file.get('path')}")

        changes: list[str] = []
        json_match = _CHANGES_FENCE_RE.search(text)
        if json_match:
            try:
                meta = json.loads(json_match.group(1).strip())
                if isinstance(meta, dict) and isinstance(meta.get("changes"), list):
                    changes = meta["changes"]
            except json.JSONDecodeError:
                pass

        return {"path": path, "content": html, "_changes": changes}

    def _parse_multi_block(self, text: str, inp: AgentInput) -> dict[str, Any]:
        """Compatibilité — non utilisé dans le run() custom."""
        matches = _FILE_BLOCK_RE.findall(text)
        if not matches:
            raise ValueError("refinement_agent: no ### FILE: ... ```html blocks found")
        normalized = []
        for path_raw, html_raw in matches:
            path = str(path_raw).strip().lstrip("/")
            html = html_raw.strip()
            if path and html:
                normalized.append({"path": path, "content": html})
        if not normalized:
            raise ValueError("refinement_agent: no valid file blocks extracted")
        changes: list[str] = []
        json_match = _CHANGES_FENCE_RE.search(text)
        if json_match:
            try:
                meta = json.loads(json_match.group(1).strip())
                if isinstance(meta, dict) and isinstance(meta.get("changes"), list):
                    changes = meta["changes"]
            except json.JSONDecodeError:
                pass
        return {"files": normalized, "changes": changes}

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        return parsed if isinstance(parsed, dict) else {}

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any] | None:
        site = inp.context.get("static_site", {})
        files = site.get("generated_files") or site.get("files") or []
        if not isinstance(files, list) or not files:
            return None
        return {"files": files, "changes": [f"fallback refinement: {error}"]}
