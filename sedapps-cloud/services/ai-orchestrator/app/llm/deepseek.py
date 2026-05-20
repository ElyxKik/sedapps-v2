"""
DeepSeek V4 adapter (OpenAI-compatible Chat Completions).

Docs : https://api-docs.deepseek.com/news/news260424
- base_url inchangé : https://api.deepseek.com/v1
- modèles : deepseek-v4-pro | deepseek-v4-flash
- Supporte le mode "thinking" (raisonnement) via le param `thinking`.
- 1M de contexte par défaut.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.llm.base import LLMResponse, LLMUsage

log = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


class DeepSeekClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        if not self.api_key:
            log.warning("DEEPSEEK_API_KEY is empty — LLM calls will fail")

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, LLMError)),
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
        if thinking:
            payload["thinking"] = {"type": "enabled"}
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_S) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if r.status_code >= 500:
                raise LLMError(f"DeepSeek {r.status_code}: {r.text[:300]}")
            if r.status_code >= 400:
                # 4xx = ne pas réessayer
                raise LLMError(f"DeepSeek {r.status_code}: {r.text[:300]}")

            data = r.json()
            choice = (data.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content") or ""
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


def get_default_client() -> DeepSeekClient:
    return DeepSeekClient()
