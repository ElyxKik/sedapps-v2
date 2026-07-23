from __future__ import annotations

from app.agents.base import DEEPSEEK_TASK_AGENTS, get_client_for_agent
from app.llm.deepseek import DeepSeekClient
from app.llm.openai_client import OpenAIClient


def test_onboarding_and_conversational_tasks_use_deepseek() -> None:
    assert DEEPSEEK_TASK_AGENTS == frozenset(
        {"onboarding_guide", "blog_writer", "component_editor", "project_chat"}
    )
    for agent_name in DEEPSEEK_TASK_AGENTS:
        assert isinstance(get_client_for_agent(agent_name), DeepSeekClient)


def test_generation_and_structural_agents_use_gpt() -> None:
    for agent_name in (
        "site_generation_agent",
        "designer",
        "site_planner",
        "static_page_builder",
        "qa",
    ):
        client = get_client_for_agent(agent_name)
        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-5.6-terra"
