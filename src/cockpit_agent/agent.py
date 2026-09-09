from __future__ import annotations

import os

from openai import AsyncOpenAI
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    set_tracing_disabled,
)
from dotenv import load_dotenv

from .tools import ALL_TOOLS

load_dotenv()

# DeepSeek 不使用 OpenAI tracing，因此关闭 Agents SDK tracing。
set_tracing_disabled(True)

INSTRUCTIONS = """
You are an AI cockpit assistant for a mock passenger vehicle.

Goals:
1. Understand natural-language cockpit requests.
2. Use tools rather than pretending an action happened.
3. Use search_vehicle_manual for questions about warning indicators,
   feature behavior, or operating instructions.
4. Respect tool-side safety rules. If a tool rejects an unsafe action,
   explain the reason briefly and do not work around it.
5. Keep answers concise and natural for an in-car voice assistant.
6. Never claim to control a real vehicle.
   This project operates on a simulated vehicle state only.

Always respond to the user in Chinese unless the user explicitly requests
another language.
""".strip()


def build_agent() -> Agent:
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
        instructions=INSTRUCTIONS,
        model=model,
        tools=ALL_TOOLS,
    )


def run_agent(user_input: str) -> str:
    result = Runner.run_sync(
        build_agent(),
        user_input,
    )

    return str(result.final_output)
