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
from app.llm.deepseek import DeepSeekClient, LLMError, get_default_client

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
    status: str = "ok"               # ok | partial | failed
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
        try:
            resp: LLMResponse = await self.client.chat(
                messages=[
                    {"role": "system", "content": self.system_prompt(inp)},
                    {"role": "user", "content": self.user_prompt(inp)},
                ],
                temperature=self.default_temperature,
                max_tokens=self.default_max_tokens,
                thinking=self.use_thinking,
                response_format_json=True,
            )
            parsed = extract_json(resp.content)
            data = self.post_process(parsed, inp)
            return AgentOutput(
                agent=self.name,
                status="ok",
                data=data,
                tokens=TokenUsage(prompt=resp.usage.prompt_tokens,
                                  completion=resp.usage.completion_tokens),
                duration_ms=int((time.perf_counter() - t0) * 1000),
                model=resp.model,
                warnings=warnings,
            )
        except (LLMError, ValueError, asyncio.TimeoutError) as e:
            log.exception("agent %s failed", self.name)
            fb = self.fallback(inp, str(e))
            if fb is None:
                return AgentOutput(
                    agent=self.name,
                    status="failed",
                    data={},
                    duration_ms=int((time.perf_counter() - t0) * 1000),
                    warnings=[f"failed: {e}"],
                )
            warnings.append(f"fallback used: {e}")
            return AgentOutput(
                agent=self.name,
                status="partial",
                data=fb,
                duration_ms=int((time.perf_counter() - t0) * 1000),
                warnings=warnings,
            )
