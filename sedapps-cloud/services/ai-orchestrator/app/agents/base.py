"""
Agent base class — every agent receives a structured JSON input and returns a
structured JSON output. The base handles LLM calls + JSON parsing + timing +
graceful error degradation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from app.llm.base import LLMResponse, extract_json
from app.llm.deepseek import DeepSeekClient, LLMError, get_default_client as _get_deepseek_client


def get_default_client() -> DeepSeekClient:
    """
    Retourne le client LLM actif selon settings.LLM_PROVIDER.
    - "deepseek"  → DeepSeekClient (défaut)
    - "openai"    → OpenAIClient (GPT-4o)
    - "anthropic" → OpenAIClient avec base_url Anthropic (Claude)
    """
    from app.config import settings  # import local pour éviter les imports circulaires
    provider = (settings.LLM_PROVIDER or "deepseek").lower()
    if provider == "openai":
        from app.llm.openai_client import get_openai_client
        return get_openai_client()  # type: ignore[return-value]
    if provider == "anthropic":
        from app.llm.openai_client import get_anthropic_client
        return get_anthropic_client()  # type: ignore[return-value]
    return _get_deepseek_client()

log = logging.getLogger(__name__)

AGENT_REGISTRY: dict[str, type["BaseAgent"]] = {}


class AgentInput(BaseModel):
    project_id: str
    job_id: str
    tenant_id: str
    locale: str = "fr"
    context: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)


class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0


class AgentOutput(BaseModel):
    agent: str
    status: str = "ok"  # ok | partial | failed
    data: dict[str, Any] = Field(default_factory=dict)
    tokens: TokenUsage = Field(default_factory=TokenUsage)
    duration_ms: int = 0
    model: str = ""
    warnings: list[str] = Field(default_factory=list)


class BaseAgent:
    name: ClassVar[str] = "base"
    prompt_version: ClassVar[int] = 1
    default_temperature: ClassVar[float] = 0.3
    default_max_tokens: ClassVar[int] = 4096
    use_thinking: ClassVar[bool] = False
    fallback_status: ClassVar[str] = "ok"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if getattr(cls, "name", None) and cls.name != "base":
            AGENT_REGISTRY[cls.name] = cls

    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self.client = client or get_default_client()

    # ── to implement in subclasses ──────────────────────────
    def system_prompt(self, inp: AgentInput) -> str:
        raise NotImplementedError

    def user_prompt(self, inp: AgentInput) -> str:
        raise NotImplementedError

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        """Validate and shape the parsed JSON. Override in subclass for stricter checks."""
        if not isinstance(parsed, dict):
            raise ValueError(f"{self.name}: expected object, got {type(parsed).__name__}")
        return parsed

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any] | None:
        """Returned when LLM fails completely; None = propagate failure."""
        return None

    # ── runner ──────────────────────────────────────────────
    async def run(self, inp: AgentInput) -> AgentOutput:
        t0 = time.perf_counter()
        warnings: list[str] = []
        max_retries = 2
        messages = [
            {"role": "system", "content": self.system_prompt(inp)},
            {"role": "user", "content": self.user_prompt(inp)},
        ]

        tokens_prompt = 0
        tokens_completion = 0
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                resp: LLMResponse = await self.client.chat(
                    messages=messages,
                    temperature=self.default_temperature,
                    max_tokens=self.default_max_tokens,
                    thinking=self.use_thinking,
                    response_format_json=True,
                )
                tokens_prompt += resp.usage.prompt_tokens
                tokens_completion += resp.usage.completion_tokens

                try:
                    parsed = extract_json(resp.content)
                    data = self.post_process(parsed, inp)

                    # Success! Return output
                    return AgentOutput(
                        agent=self.name,
                        status="ok",
                        data=data,
                        tokens=TokenUsage(prompt=tokens_prompt, completion=tokens_completion),
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        model=resp.model,
                        warnings=warnings,
                    )
                except (ValueError, KeyError, TypeError) as parse_or_val_err:
                    last_error = parse_or_val_err
                    if attempt < max_retries:
                        log.warning(
                            "Agent %s failed to output valid schema on attempt %d/%d: %s. Retrying self-correction...",
                            self.name,
                            attempt + 1,
                            max_retries + 1,
                            parse_or_val_err,
                        )
                        warnings.append(f"Attempt {attempt + 1} failed: {parse_or_val_err}")

                        # Append the assistant's broken message and a user correction prompt
                        messages.append({"role": "assistant", "content": resp.content})
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    f"La réponse précédente a généré l'erreur suivante lors du traitement :\n"
                                    f"'{parse_or_val_err}'\n\n"
                                    f"Génère à nouveau la réponse complète au format JSON STRICTEMENT VALIDE. "
                                    f"Fais extrêmement attention aux guillemets doubles, aux virgules et à la structure attendue."
                                ),
                            }
                        )
                        continue
                    else:
                        raise parse_or_val_err

            except (LLMError, ValueError, KeyError, TypeError, asyncio.TimeoutError) as e:
                # If we have reached the last attempt, or if it's an LLM connection error that we shouldn't retry standardly
                last_error = e
                if attempt == max_retries:
                    break

        # If we got here, all attempts failed. Use fallback.
        log.warning(
            "agent %s used fallback after failing all attempts. Last error: %s",
            self.name,
            last_error,
        )
        fb = self.fallback(inp, str(last_error))
        if fb is None:
            log.exception("agent %s failed completely", self.name)
            return AgentOutput(
                agent=self.name,
                status="failed",
                data={},
                tokens=TokenUsage(prompt=tokens_prompt, completion=tokens_completion),
                duration_ms=int((time.perf_counter() - t0) * 1000),
                warnings=[f"failed: {last_error}"],
            )
        warnings.append(f"fallback used: {last_error}")
        return AgentOutput(
            agent=self.name,
            status=self.fallback_status,
            data=fb,
            tokens=TokenUsage(prompt=tokens_prompt, completion=tokens_completion),
            duration_ms=int((time.perf_counter() - t0) * 1000),
            warnings=warnings,
        )
