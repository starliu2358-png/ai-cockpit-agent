import json

from cockpit_agent import ui
from cockpit_agent.vehicle_book.admin import load_knowledge_admin_view


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


def test_chat_and_mock_vehicle_state_helpers_remain_available() -> None:
    assert ui.chat("   ") == "请输入一句座舱指令。"
    state = json.loads(ui.set_mock_speed(50))
    assert state["speed_kph"] == 50.0

    speed, reset_state = ui.reset_state()
    assert speed == 0.0
    assert json.loads(reset_state)["speed_kph"] == 0.0
