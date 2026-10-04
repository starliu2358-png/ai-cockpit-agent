from types import SimpleNamespace

from cockpit_agent import agent
from cockpit_agent.tools import ALL_TOOLS


def test_agent_binds_vehicle_knowledge_per_request_and_separates_legacy_manual() -> None:
    names = {tool.name for tool in ALL_TOOLS}

    assert "vehicle_knowledge" not in names
    assert "search_vehicle_manual" in names
    bound_tools = agent._tools_for_request("alpha_aster_x1_max_v1", False)
    knowledge_tool = next(tool for tool in bound_tools if tool.name == "vehicle_knowledge")
    assert set(knowledge_tool.params_json_schema["properties"]) == {"question"}
    instructions = agent._instructions("alpha_aster_x1_max_v1", False)
    assert "vehicle_knowledge" in instructions
    assert "search_vehicle_manual" in instructions
    assert "alpha_aster_x1_max_v1" in instructions


def test_run_agent_passes_explicit_vehicle_context_without_network(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_build_agent(**kwargs):
        calls["context"] = kwargs
        return "fake-agent"

    def fake_run_sync(built_agent, user_input):
        calls["agent"] = built_agent
        calls["input"] = user_input
        return SimpleNamespace(final_output="离线工具结果")

    monkeypatch.setattr(agent, "build_agent", fake_build_agent)
    monkeypatch.setattr(agent.Runner, "run_sync", fake_run_sync)

    assert agent.run_agent("LCC", vehicle_id="alpha_aster_x1_max_v2", include_pre_release=True) == "离线工具结果"
    assert calls["context"] == {"vehicle_id": "alpha_aster_x1_max_v2", "include_pre_release": True}
    assert calls["input"] == "LCC"


def test_agent_instructions_require_context_when_none_selected() -> None:
    instructions = agent._instructions(None, False)

    assert "No Vehicle Profile has been selected" in instructions
    assert "Do not call vehicle_knowledge" in instructions
