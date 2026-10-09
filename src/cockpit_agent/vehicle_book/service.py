from __future__ import annotations

from typing import Protocol

from .answerer import (
    AnswerDraft,
    AnswerDraftError,
    DeepSeekAnswerGenerator,
    EvidenceAnswerer,
    GroundedAnswerer,
)
from .registry import RegistryError, VehicleRegistry
from .retriever import VehicleBookRetriever
from .schemas import AnswerResult, Citation, RetrievedChunk

FALLBACK_ANSWER = "未在当前车辆资料中找到足够可靠的依据。"


class EvidenceRetriever(Protocol):
    def retrieve(
        self,
        vehicle_id: str,
        query: str,
        top_k: int = 2,
        *,
        include_pre_release: bool = False,
    ) -> tuple[RetrievedChunk, ...]: ...


class DraftAnswerer(Protocol):
    def generate_draft(
        self,
        vehicle_id: str,
        question: str,
        evidence: tuple[RetrievedChunk, ...],
    ) -> AnswerDraft: ...


class VehicleBookService:
    """Orchestrate exact-profile retrieval and grounded answer construction."""

    def __init__(
        self,
        vehicle_registry: VehicleRegistry | None = None,
        retriever: EvidenceRetriever | None = None,
        answerer: DraftAnswerer | None = None,
    ) -> None:
        self.vehicle_registry = vehicle_registry or VehicleRegistry()
        self.retriever = retriever or VehicleBookRetriever(
            vehicle_registry=self.vehicle_registry
        )
        self.answerer = answerer or self._default_answerer()

    @staticmethod
    def _default_answerer() -> DraftAnswerer:
        try:
            return GroundedAnswerer(DeepSeekAnswerGenerator.from_env())
        except ValueError as exc:
            if "DEEPSEEK_API_KEY" not in str(exc):
                raise
            return EvidenceAnswerer()

    def answer(
        self,
        question: str,
        vehicle_id: str,
        top_k: int = 4,
        *,
        include_pre_release: bool = False,
    ) -> AnswerResult:
        profile = self.vehicle_registry.resolve(vehicle_id)
        if profile.release_status == "pre_release" and not include_pre_release:
            raise RegistryError(
                f"Vehicle '{profile.vehicle_id}' is pre_release; "
                "pass include_pre_release=True to retrieve its documents"
            )

        evidence = self.retriever.retrieve(
            profile.vehicle_id,
            question,
            top_k=top_k,
            include_pre_release=include_pre_release,
        )
        if not evidence:
            return self._fallback(
                profile.vehicle_id,
                evidence,
                reason="no_retrieval_results",
            )

        if any(
            result.chunk.metadata.vehicle_id != profile.vehicle_id
            for result in evidence
        ):
            return self._fallback(
                profile.vehicle_id,
                (),
                reason="invalid_retrieval_evidence",
            )

        try:
            draft = self.answerer.generate_draft(
                profile.vehicle_id,
                question,
                evidence,
            )
        except AnswerDraftError as exc:
            return self._fallback(
                profile.vehicle_id,
                evidence,
                reason=self._draft_error_reason(exc),
            )

        if draft.insufficient_evidence:
            return self._fallback(
                profile.vehicle_id,
                evidence,
                reason="insufficient_evidence",
            )

        evidence_by_id = {
            result.chunk.chunk_id: result
            for result in evidence
        }
        if not draft.cited_chunk_ids:
            return self._fallback(
                profile.vehicle_id,
                evidence,
                reason="missing_citation_ids",
            )

        try:
            matched = tuple(
                evidence_by_id[chunk_id]
                for chunk_id in draft.cited_chunk_ids
            )
        except KeyError:
            return self._fallback(
                profile.vehicle_id,
                evidence,
                reason="unknown_citation_ids",
            )

        citations = tuple(
            Citation.from_retrieved(result)
            for result in self._preferred_citation_evidence(matched)
        )
        return AnswerResult(
            answer=draft.answer,
            vehicle_id=profile.vehicle_id,
            citations=citations,
            evidence=evidence,
        )

    @staticmethod
    def _fallback(
        vehicle_id: str,
        evidence: tuple[RetrievedChunk, ...],
        *,
        reason: str,
    ) -> AnswerResult:
        return AnswerResult(
            answer=FALLBACK_ANSWER,
            vehicle_id=vehicle_id,
            citations=(),
            evidence=evidence,
            fallback_reason=reason,
        )

    @staticmethod
    def _preferred_citation_evidence(
        cited_evidence: tuple[RetrievedChunk, ...],
    ) -> tuple[RetrievedChunk, ...]:
        """Prefer detailed source material over a redundant configuration summary.

        Configuration chunks help retrieval and answer generation, but a detailed
        manual or ADAS section is the more precise provenance when both are cited.
        Keep configuration evidence when it is the only source the draft selected.
        """
        detailed = tuple(
            result
            for result in cited_evidence
            if result.chunk.metadata.content_type != "configuration"
        )
        return detailed or cited_evidence

    @staticmethod
    def _draft_error_reason(error: AnswerDraftError) -> str:
        message = str(error)
        if "not supplied as evidence" in message:
            return "unknown_citation_ids"
        if "at least one citation" in message:
            return "missing_citation_ids"
        return "malformed_model_output"
