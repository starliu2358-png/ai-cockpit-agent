from __future__ import annotations

import json

import gradio as gr

from .agent import run_agent
from .state import vehicle_state


def chat(message: str, history: list[dict] | None = None) -> str:
    _ = history

    if not message.strip():
        return "请输入一句座舱指令。"

    try:
        return run_agent(message)
    except Exception as exc:
        return f"运行失败：{exc}"


def state_json() -> str:
    return json.dumps(
        vehicle_state.snapshot(),
        ensure_ascii=False,
        indent=2,
    )


def reset_state() -> tuple[float, str]:
    state = vehicle_state.reset()

    return (
        0.0,
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
    )


def set_mock_speed(speed_kph: float) -> str:
    state = vehicle_state.update(
        speed_kph=round(float(speed_kph), 1)
    )

    return json.dumps(
        state,
        ensure_ascii=False,
        indent=2,
    )


def build_demo() -> gr.Blocks:

    with gr.Blocks(
        title="AI Cockpit Agent"
    ) as demo:

        gr.Markdown(
            """
# AI Cockpit Agent

**LLM Agent + Tool Calling + Manual RAG + Safety Guardrails**

> Demo 使用 Mock Vehicle State，不连接真实车辆。
"""
        )

        gr.ChatInterface(
            fn=chat,
            examples=[
                "我有点冷，把空调调到23度",
                "把主驾座椅加热调到2档",
                "胎压报警灯亮了是什么意思？",
                "导航到北京南站",
                "帮我打开左前门",
            ],
        )

        gr.Markdown("## Mock Vehicle State")

        speed_slider = gr.Slider(
            minimum=0,
            maximum=120,
            value=0,
            step=10,
            label="模拟车辆速度 km/h",
        )

        with gr.Row():

            state_btn = gr.Button(
                "查看车辆状态"
            )

            reset_btn = gr.Button(
                "重置车辆状态"
            )

        state_box = gr.Code(
            label="Mock Vehicle State",
            language="json",
            value=state_json(),
        )

        speed_slider.change(
            fn=set_mock_speed,
            inputs=speed_slider,
            outputs=state_box,
        )

        state_btn.click(
            fn=state_json,
            outputs=state_box,
        )

        reset_btn.click(
            fn=reset_state,
            outputs=[
                speed_slider,
                state_box,
            ],
        )

    return demo


def main() -> None:
    build_demo().launch()


if __name__ == "__main__":
    main()