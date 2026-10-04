"""Thin, controlled Agent-tool adapter for Vehicle Book answers."""

from __future__ import annotations

from typing import Protocol

from agents import function_tool

from .registry import RegistryError
from .schemas import AnswerResult
from .service import VehicleBookService


class VehicleKnowledgeService(Protocol):
    def answer(
        self,
        question: str,
        vehicle_id: str,
        top_k: int = 4,
        *,
        include_pre_release: bool = False,
    ) -> AnswerResult: ...


def _fallback(vehicle_id: str, answer: str, reason: str) -> dict[str, object]:
    return {
        "answer": answer,
        "vehicle_id": vehicle_id,
        "citations": [],
        "is_fallback": True,
        "fallback_reason": reason,
    }


def vehicle_knowledge_result(
    question: str,
    vehicle_id: str,
    include_pre_release: bool = False,
    *,
    service: VehicleKnowledgeService | None = None,
) -> dict[str, object]:
    """Return one exact-profile Vehicle Book result without changing any state."""
    question = question.strip()
    vehicle_id = vehicle_id.strip()
    if not vehicle_id:
        return _fallback(
            "",
            "请先选择或明确提供车辆 Profile 后再查询车辆知识。",
            "missing_vehicle_context",
        )
    if not question:
        return _fallback(vehicle_id, "请提供需要查询的车辆问题。", "missing_question")
    try:
        result = (service or VehicleBookService()).answer(
            question,
            vehicle_id,
            include_pre_release=include_pre_release,
        )
    except RegistryError as exc:
        return _fallback(vehicle_id, f"无法使用该车辆 Profile：{exc}", "invalid_vehicle_context")

    return {
        "answer": result.answer,
        "vehicle_id": result.vehicle_id,
        "citations": [
            {
                "document_id": citation.document_id,
                "title": citation.title,
                "section": citation.section,
                "document_version": citation.document_version,
                "vehicle_id": citation.vehicle_id,
                "source_path": citation.source_path.as_posix(),
            }
            for citation in result.citations
        ],
        "is_fallback": result.is_fallback,
        "fallback_reason": result.fallback_reason,
    }


def create_vehicle_knowledge_tool(
    selected_vehicle_id: str | None,
    allow_pre_release: bool,
    *,
    service: VehicleKnowledgeService | None = None,
):
    """Create a request-bound Agent tool whose schema exposes only ``question``.

    The closure captures UI/request policy. Model-generated tool JSON therefore cannot
    replace the selected Profile or enable pre-release access.
    """
    vehicle_id = selected_vehicle_id or ""

    @function_tool(name_override="vehicle_knowledge")
    def vehicle_knowledge(question: str) -> dict[str, object]:
        """Answer a vehicle-specific knowledge question for the currently selected Profile.

        The selected Profile and its release policy are fixed for this request. If no
        Profile was selected, return a safe request for the user to select one.
        """
        return vehicle_knowledge_result(
            question,
            vehicle_id,
            allow_pre_release,
            service=service,
        )

    return vehicle_knowledge
