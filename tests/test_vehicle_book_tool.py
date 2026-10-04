import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path

from agents.tool_context import ToolContext

from cockpit_agent.state import vehicle_state
from cockpit_agent.vehicle_book.registry import RegistryError
from cockpit_agent.vehicle_book.schemas import AnswerResult, Citation
from cockpit_agent.vehicle_book.tool import (
    create_vehicle_knowledge_tool,
    vehicle_knowledge_result,
)


def _result(vehicle_id: str, version: str, answer: str, *, fallback: str | None = None) -> AnswerResult:
    citation = Citation(
        chunk_id=f"{vehicle_id}:lcc",
        document_id=f"{vehicle_id}_adas",
        vehicle_id=vehicle_id,
        title=f"Vehicle {version} ADAS Guide",
        document_version=version,
        section="LCC",
        source_path=Path(f"data/knowledge/{vehicle_id}/adas.md"),
        rank=1,
        score=1.0,
    )
    return AnswerResult(answer, vehicle_id, citations=(citation,) if fallback is None else (), fallback_reason=fallback)


@dataclass
class FakeService:
    calls: list[tuple[str, str, bool]] = field(default_factory=list)

    def answer(self, question: str, vehicle_id: str, top_k: int = 4, *, include_pre_release: bool = False) -> AnswerResult:
        self.calls.append((question, vehicle_id, include_pre_release))
        if vehicle_id == "alpha_aster_x1_max_v2" and not include_pre_release:
            raise RegistryError("pre_release requires explicit opt-in")
        if vehicle_id == "alpha_aster_x1_max_v1":
            return _result(vehicle_id, "1.0", "V1 的 LCC 仅可在 60–120 km/h 使用。")
        if vehicle_id == "alpha_aster_x1_max_v2":
            return _result(vehicle_id, "2.0", "V2 的 LCC 可在 0–130 km/h 使用。")
        if vehicle_id == "alpha_aster_x2_max_v1":
            return _result(vehicle_id, "1.0", "最大直流快充功率为 240 kW。")
        return _result(vehicle_id, "1.0", "资料不足。", fallback="no_retrieval_results")


def test_tool_keeps_x1_versions_and_citations_profile_scoped() -> None:
    service = FakeService()
    v1 = vehicle_knowledge_result("30 km/h 能开启 LCC 吗？", "alpha_aster_x1_max_v1", service=service)
    v2 = vehicle_knowledge_result("30 km/h 能开启 LCC 吗？", "alpha_aster_x1_max_v2", True, service=service)

    assert "60–120" in v1["answer"]
    assert "0–130" in v2["answer"]
    assert v1["citations"][0]["vehicle_id"] == "alpha_aster_x1_max_v1"
    assert v2["citations"][0]["document_version"] == "2.0"
    assert service.calls[1][2] is True


def test_tool_requires_explicit_pre_release_access_and_never_defaults_vehicle() -> None:
    service = FakeService()
    blocked = vehicle_knowledge_result("LCC", "alpha_aster_x1_max_v2", service=service)
    missing = vehicle_knowledge_result("LCC", "", service=service)
    unknown = vehicle_knowledge_result("LCC", "unknown", service=service)

    assert blocked["is_fallback"] is True
    assert blocked["fallback_reason"] == "invalid_vehicle_context"
    assert missing["fallback_reason"] == "missing_vehicle_context"
    assert unknown["vehicle_id"] == "unknown"
    assert unknown["is_fallback"] is True


def test_tool_preserves_x2_answer_fallback_reason_and_mock_state() -> None:
    service = FakeService()
    vehicle_state.reset()
    before = vehicle_state.snapshot()
    x2 = vehicle_knowledge_result("最大直流快充功率？", "alpha_aster_x2_max_v1", service=service)
    fallback = vehicle_knowledge_result("无依据问题", "unknown", service=service)

    assert "240 kW" in x2["answer"]
    assert x2["citations"][0]["vehicle_id"] == "alpha_aster_x2_max_v1"
    assert fallback["fallback_reason"] == "no_retrieval_results"
    assert vehicle_state.snapshot() == before


def test_request_bound_tool_hides_and_forces_profile_and_release_policy() -> None:
    service = FakeService()
    tool = create_vehicle_knowledge_tool(
        "alpha_aster_x1_max_v1",
        False,
        service=service,
    )

    assert set(tool.params_json_schema["properties"]) == {"question"}
    assert "vehicle_id" not in tool.params_json_schema["properties"]
    assert "include_pre_release" not in tool.params_json_schema["properties"]

    context = ToolContext(
        context=None,
        tool_name="vehicle_knowledge",
        tool_call_id="test-call",
        tool_arguments="{}",
    )
    result = asyncio.run(
        tool.on_invoke_tool(context, json.dumps({"question": "30 km/h 能开启 LCC 吗？"}))
    )
    assert result["vehicle_id"] == "alpha_aster_x1_max_v1"
    assert service.calls[-1] == ("30 km/h 能开启 LCC 吗？", "alpha_aster_x1_max_v1", False)

    # Even if a model emits ignored extra fields, the bound closure invokes only
    # the selected X1 V1 Profile with the UI policy; it never uses those values.
    attempted_override = asyncio.run(
        tool.on_invoke_tool(
            context,
            json.dumps(
                {
                    "question": "30 km/h 能开启 LCC 吗？",
                    "vehicle_id": "alpha_aster_x2_max_v1",
                    "include_pre_release": True,
                }
            ),
        )
    )
    assert attempted_override["vehicle_id"] == "alpha_aster_x1_max_v1"
    assert service.calls[-1] == ("30 km/h 能开启 LCC 吗？", "alpha_aster_x1_max_v1", False)


def test_request_bound_tool_keeps_pre_release_disabled_until_ui_opt_in() -> None:
    service = FakeService()
    context = ToolContext(
        context=None,
        tool_name="vehicle_knowledge",
        tool_call_id="test-pre-release",
        tool_arguments="{}",
    )
    denied_tool = create_vehicle_knowledge_tool("alpha_aster_x1_max_v2", False, service=service)
    denied = asyncio.run(
        denied_tool.on_invoke_tool(
            context,
            json.dumps({"question": "LCC", "include_pre_release": True}),
        )
    )
    allowed_tool = create_vehicle_knowledge_tool("alpha_aster_x1_max_v2", True, service=service)
    allowed = asyncio.run(
        allowed_tool.on_invoke_tool(context, json.dumps({"question": "LCC"}))
    )

    assert denied["fallback_reason"] == "invalid_vehicle_context"
    assert allowed["vehicle_id"] == "alpha_aster_x1_max_v2"
    assert allowed["is_fallback"] is False
    assert service.calls == [
        ("LCC", "alpha_aster_x1_max_v2", False),
        ("LCC", "alpha_aster_x1_max_v2", True),
    ]
