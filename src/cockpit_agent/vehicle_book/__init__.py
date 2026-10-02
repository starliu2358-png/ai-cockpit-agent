"""Vehicle-aware knowledge models and local registries."""

from .registry import DocumentRegistry, RegistryError, VehicleRegistry
from .schemas import (
    AnswerDraft,
    AnswerResult,
    Citation,
    DocumentMetadata,
    KnowledgeChunk,
    RetrievedChunk,
    VehicleProfile,
)

__all__ = [
    "AnswerDraft",
    "AnswerResult",
    "Citation",
    "DocumentMetadata",
    "DocumentRegistry",
    "KnowledgeChunk",
    "RegistryError",
    "RetrievedChunk",
    "VehicleProfile",
    "VehicleRegistry",
]
