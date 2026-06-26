"""
Client OpenAI-compatible — supporte OpenAI GPT-4o et Anthropic Claude (via leur API OpenAI-compatible).

Ce client implémente la même interface que DeepSeekClient (.chat()) pour être
interchangeable dans BaseAgent et partout où get_default_client() est appelé.

Configuration .env :
  LLM_PROVIDER=openai         → GPT-4o via api.openai.com
  LLM_PROVIDER=anthropic      → Claude via api.anthropic.com (mode OpenAI-compat)

  OPENAI_API_KEY=sk-...
  OPENAI_BASE_URL=https://api.openai.com/v1        (optionnel)
  OPENAI_MODEL=gpt-4o                               (optionnel)

  ANTHROPIC_API_KEY=sk-ant-...
  ANTHROPIC_BASE_URL=https://api.anthropic.com/v1  (optionnel)
  ANTHROPIC_MODEL=claude-sonnet-4-5                 (optionnel)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.llm.base import LLMResponse, LLMUsage
from app.llm.deepseek import LLMError, RetryableLLMError, FatalLLMError

log = logging.getLogger(__name__)


class OpenAIClient:
    """Client HTTP pour l'API OpenAI (et ses compatibles : Anthropic, Azure, Mistral…)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        provider: str = "openai",
    ) -> None:
        self.provider = provider.lower()

        if self.provider == "anthropic":
            self.api_key = api_key or settings.ANTHROPIC_API_KEY
            self.base_url = (base_url or settings.ANTHROPIC_BASE_URL).rstrip("/")
            self.model = model or settings.ANTHROPIC_MODEL
        else:
            # Défaut : OpenAI
            self.api_key = api_key or settings.OPENAI_API_KEY
            self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
            self.model = model or settings.OPENAI_MODEL

        if not self.api_key:
            log.warning("%s API key is empty — LLM calls will fail", self.provider.upper())

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, RetryableLLMError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        thinking: bool = False,
        response_format_json: bool = False,
        model: str | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        # OpenAI JSON mode — Anthropic ne supporte pas response_format de la même façon
        if response_format_json and self.provider != "anthropic":
            payload["response_format"] = {"type": "json_object"}

        # Note : le paramètre `thinking` n'est pas supporté par l'API OpenAI standard.
        # Pour Claude extended thinking, utiliser l'API native Anthropic — ignoré ici.
        if thinking:
            log.debug("OpenAIClient: 'thinking' param ignored (not supported in OpenAI-compat mode)")

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Anthropic requiert un header anthropic-version
        if self.provider == "anthropic":
            headers["anthropic-version"] = "2023-06-01"

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_S) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            if r.status_code >= 500:
                raise RetryableLLMError(f"{self.provider} {r.status_code}: {r.text[:300]}")
            if r.status_code >= 400:
                raise FatalLLMError(f"{self.provider} {r.status_code}: {r.text[:300]}")

            data = r.json()
            choice = (data.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content") or ""
            if not content.strip():
                raise RetryableLLMError("empty LLM response")
            usage = data.get("usage") or {}
            return LLMResponse(
                content=content,
                model=data.get("model") or payload["model"],
                usage=LLMUsage(
                    prompt_tokens=int(usage.get("prompt_tokens", 0)),
                    completion_tokens=int(usage.get("completion_tokens", 0)),
                ),
                raw=data,
            )


def get_openai_client(model: str | None = None) -> OpenAIClient:
    return OpenAIClient(provider="openai", model=model)


def get_anthropic_client(model: str | None = None) -> OpenAIClient:
    return OpenAIClient(provider="anthropic", model=model)
