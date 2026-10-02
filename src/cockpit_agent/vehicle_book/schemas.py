from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar


def _required_text(data: dict[str, Any], field_name: str) -> str:
    value = data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True, slots=True)
class VehicleProfile:
    vehicle_id: str
    oem: str
    model: str
    trim: str
    software_version: str
    release_status: str

    VALID_RELEASE_STATUSES: ClassVar[frozenset[str]] = frozenset({"released", "pre_release"})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VehicleProfile:
        profile = cls(
            vehicle_id=_required_text(data, "vehicle_id"),
            oem=_required_text(data, "oem"),
            model=_required_text(data, "model"),
            trim=_required_text(data, "trim"),
            software_version=_required_text(data, "software_version"),
            release_status=_required_text(data, "release_status"),
        )
        if profile.release_status not in cls.VALID_RELEASE_STATUSES:
            raise ValueError(
                "release_status must be one of: " + ", ".join(sorted(cls.VALID_RELEASE_STATUSES))
            )
        return profile


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    document_id: str
    vehicle_id: str
    title: str
    content_type: str
    document_version: str
    source_path: Path
    status: str
    locale: str = "zh-CN"
    supersedes: str | None = None

    VALID_STATUSES: ClassVar[frozenset[str]] = frozenset(
        {"draft", "review", "published", "retired"}
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentMetadata:
        supersedes = data.get("supersedes")
        if supersedes is not None and (not isinstance(supersedes, str) or not supersedes.strip()):
            raise ValueError("supersedes must be a non-empty string when provided")

        metadata = cls(
            document_id=_required_text(data, "document_id"),
            vehicle_id=_required_text(data, "vehicle_id"),
            title=_required_text(data, "title"),
            content_type=_required_text(data, "content_type"),
            document_version=_required_text(data, "document_version"),
            source_path=Path(_required_text(data, "source_path")),
            status=_required_text(data, "status"),
            locale=_required_text(data, "locale"),
            supersedes=supersedes.strip() if supersedes else None,
        )
        if metadata.status not in cls.VALID_STATUSES:
            raise ValueError("status must be one of: " + ", ".join(sorted(cls.VALID_STATUSES)))
        if metadata.source_path.is_absolute():
            raise ValueError("source_path must be relative to the repository root")
        return metadata


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    chunk_id: str
    section: str
    text: str
    metadata: DocumentMetadata


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk: KnowledgeChunk
    score: float
    rank: int


@dataclass(frozen=True, slots=True)
class Citation:
    chunk_id: str
    document_id: str
    vehicle_id: str
    title: str
    document_version: str
    section: str
    source_path: Path
    rank: int
    score: float

    @classmethod
    def from_retrieved(cls, retrieved: RetrievedChunk) -> Citation:
        """Build citation provenance from an actual retrieval result."""
        chunk = retrieved.chunk
        metadata = chunk.metadata
        return cls(
            chunk_id=chunk.chunk_id,
            document_id=metadata.document_id,
            vehicle_id=metadata.vehicle_id,
            title=metadata.title,
            document_version=metadata.document_version,
            section=chunk.section,
            source_path=metadata.source_path,
            rank=retrieved.rank,
            score=retrieved.score,
        )


@dataclass(frozen=True, slots=True)
class AnswerDraft:
    answer: str
    cited_chunk_ids: tuple[str, ...]
    insufficient_evidence: bool


@dataclass(frozen=True, slots=True)
class AnswerResult:
    answer: str
    vehicle_id: str
    citations: tuple[Citation, ...] = field(default_factory=tuple)
    evidence: tuple[RetrievedChunk, ...] = field(default_factory=tuple)
    fallback_reason: str | None = None

    @property
    def is_fallback(self) -> bool:
        return self.fallback_reason is not None
