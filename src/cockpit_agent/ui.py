from __future__ import annotations

import json

import gradio as gr

from .agent import run_agent
from .state import vehicle_state
from .vehicle_book.admin import KnowledgeAdminView, load_knowledge_admin_view


def chat(message: str, history: list[dict] | None = None) -> str:
    _ = history

    if not message.strip():
        return "请输入一句座舱指令。"

    try:
        return run_agent(message)
    except Exception as exc:  # noqa: BLE001 - UI boundary must render agent failures safely.
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


def admin_document_rows(view: KnowledgeAdminView, vehicle_id: str) -> list[list[str]]:
    """Return only the selected profile's safe document metadata for Gradio."""
    profile = next((item for item in view.profiles if item.vehicle_id == vehicle_id), None)
    if profile is None:
        return []
    return [
        [
            document.document_id,
            document.title,
            document.content_type,
            document.document_version,
            document.status,
            document.locale,
            document.source_path,
        ]
        for document in profile.documents
    ]


def admin_gate_rows(view: KnowledgeAdminView) -> list[list[str]]:
    return [
        [
            gate.name,
            gate.category,
            gate.hard_or_soft,
            gate.threshold,
            gate.status,
            gate.reason,
            gate.evidence_path,
        ]
        for gate in view.release_gate.gates
    ]


def admin_gate_markdown(view: KnowledgeAdminView) -> str:
    gate = view.release_gate
    return f"### Release Gate：`{gate.status}`\n\n{gate.message}\n\n报告路径：`{gate.report_path}`"


def build_demo() -> gr.Blocks:

    admin_view = load_knowledge_admin_view()
    default_profile = admin_view.profiles[0] if admin_view.profiles else None

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

        with gr.Tab("Cockpit Demo"):
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
                state_btn = gr.Button("查看车辆状态")
                reset_btn = gr.Button("重置车辆状态")

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
            state_btn.click(fn=state_json, outputs=state_box)
            reset_btn.click(fn=reset_state, outputs=[speed_slider, state_box])

        with gr.Tab("Knowledge Admin（只读）"):
            gr.Markdown(
                "本项目为本地模拟，不控制真实车辆。此页面仅浏览本地 Registry 和既有门禁报告。"
            )
            profile_choices = [(profile.label, profile.vehicle_id) for profile in admin_view.profiles]
            profile_selector = gr.Dropdown(
                choices=profile_choices,
                value=default_profile.vehicle_id if default_profile else None,
                label="Vehicle Profile",
                interactive=True,
            )
            document_table = gr.Dataframe(
                headers=["Document ID", "标题", "类型", "版本", "状态", "Locale", "source_path"],
                value=admin_document_rows(admin_view, default_profile.vehicle_id)
                if default_profile
                else [],
                interactive=False,
                label="适用文档（只读）",
            )
            profile_selector.change(
                fn=lambda vehicle_id: admin_document_rows(admin_view, vehicle_id),
                inputs=profile_selector,
                outputs=document_table,
            )
            gr.Markdown(admin_gate_markdown(admin_view))
            with gr.Accordion("Release Gate 明细（只读）", open=False):
                gr.Dataframe(
                    headers=["名称", "类别", "级别", "阈值", "状态", "原因", "证据路径"],
                    value=admin_gate_rows(admin_view),
                    interactive=False,
                    label="既有报告明细",
                )

    return demo


def main() -> None:
    build_demo().launch()


if __name__ == "__main__":
    main()
