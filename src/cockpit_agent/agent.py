from __future__ import annotations

import os

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

from .tools import ALL_TOOLS
from .vehicle_book.tool import create_vehicle_knowledge_tool

load_dotenv()

# DeepSeek 不使用 OpenAI tracing，因此关闭 Agents SDK tracing。
set_tracing_disabled(True)

INSTRUCTIONS = """
You are an AI cockpit assistant for a mock passenger vehicle.

Goals:
1. Understand natural-language cockpit requests.
2. Use tools rather than pretending an action happened.
3. For vehicle/model/version-specific knowledge questions, use vehicle_knowledge
   with the explicit Vehicle Profile context. Do not use search_vehicle_manual for
   profile-specific facts. search_vehicle_manual is legacy generic-manual lookup only.
4. If no explicit Vehicle Profile context is available, ask for the minimum required
   vehicle_id; never invent a model, version, or pre-release access policy.
5. When vehicle_knowledge returns citations, include a concise source summary with
   document title, section, applicable vehicle/version. Preserve fallback wording and
   fallback_reason rather than converting it into a definite factual answer.
6. Respect tool-side safety rules. If a tool rejects an unsafe action,
   explain the reason briefly and do not work around it.
7. Keep answers concise and natural for an in-car voice assistant.
8. Never claim to control a real vehicle.
   This project operates on a simulated vehicle state only.

Always respond to the user in Chinese unless the user explicitly requests
another language.
""".strip()


def _instructions(vehicle_id: str | None, include_pre_release: bool) -> str:
    if vehicle_id and vehicle_id.strip():
        return (
            f"{INSTRUCTIONS}\n\nExplicit UI Vehicle Profile: {vehicle_id.strip()}. "
            f"Pre-release access explicitly allowed: {include_pre_release}. "
            "For profile-specific knowledge, use vehicle_knowledge; its Profile and release "
            "policy are programmatically bound to this request."
        )
    return (
        f"{INSTRUCTIONS}\n\nNo Vehicle Profile has been selected. Do not call "
        "vehicle_knowledge until the user provides an explicit vehicle_id."
    )


def _tools_for_request(vehicle_id: str | None, include_pre_release: bool) -> list[object]:
    """Bind the only profile-aware tool to explicit request context."""
    return [
        *ALL_TOOLS,
        create_vehicle_knowledge_tool(vehicle_id, include_pre_release),
    ]


def build_agent(
    *, vehicle_id: str | None = None, include_pre_release: bool = False
) -> Agent:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    if not api_key:
        raise ValueError(
            "未找到 DEEPSEEK_API_KEY，请在项目根目录的 .env 文件中配置。"
        )

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    model = OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=client,
    )

    return Agent(
        name="AI Cockpit Agent",
        instructions=_instructions(vehicle_id, include_pre_release),
        model=model,
        tools=_tools_for_request(vehicle_id, include_pre_release),
    )


def run_agent(
    user_input: str,
    *,
    vehicle_id: str | None = None,
    include_pre_release: bool = False,
) -> str:
    result = Runner.run_sync(
        build_agent(
            vehicle_id=vehicle_id,
            include_pre_release=include_pre_release,
        ),
        user_input,
    )

    return str(result.final_output)
