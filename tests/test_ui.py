import json

from cockpit_agent import ui
from cockpit_agent.vehicle_book.admin import load_knowledge_admin_view
from cockpit_agent.vehicle_book.dashboard import load_evaluation_dashboard


def test_knowledge_admin_helpers_only_return_selected_profile_documents() -> None:
    view = load_knowledge_admin_view()
    selected = view.profiles[0]

    rows = ui.admin_document_rows(view, selected.vehicle_id)

    assert rows
    assert {row[0] for row in rows} == {
        document.document_id for document in selected.documents
    }
    assert ui.admin_document_rows(view, "unknown-profile") == []
    assert ".env" not in json.dumps(rows)


def test_build_demo_contains_read_only_knowledge_admin_tab() -> None:
    demo = ui.build_demo()
    config = json.dumps(demo.get_config_file(), ensure_ascii=False, default=str)

    assert "Knowledge Admin（只读）" in config
    assert "适用文档（只读）" in config
    assert "本项目为本地模拟，不控制真实车辆" in config
    assert "Evaluation Dashboard" in config
    assert "Category / Slice Metrics" in config


def test_dashboard_helpers_preserve_metrics_and_day_8_admin_data() -> None:
    dashboard = load_evaluation_dashboard()
    admin = load_knowledge_admin_view()

    assert ui.dashboard_metric_rows(dashboard.retrieval_metrics)[0][0] == "Recall@K"
    assert ui.dashboard_slice_rows(dashboard)
    assert ui.admin_document_rows(admin, admin.profiles[0].vehicle_id)


def test_chat_and_mock_vehicle_state_helpers_remain_available() -> None:
    assert ui.chat("   ") == "请输入一句座舱指令。"
    state = json.loads(ui.set_mock_speed(50))
    assert state["speed_kph"] == 50.0

    speed, reset_state = ui.reset_state()
    assert speed == 0.0
    assert json.loads(reset_state)["speed_kph"] == 0.0


def test_chat_passes_explicit_vehicle_context_to_agent(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_agent(message: str, **kwargs: object) -> str:
        captured["message"] = message
        captured.update(kwargs)
        return "知识回答"

    monkeypatch.setattr(ui, "run_agent", fake_run_agent)

    assert ui.chat("LCC", vehicle_id="alpha_aster_x1_max_v2", include_pre_release=True) == "知识回答"
    assert captured == {
        "message": "LCC",
        "vehicle_id": "alpha_aster_x1_max_v2",
        "include_pre_release": True,
    }
