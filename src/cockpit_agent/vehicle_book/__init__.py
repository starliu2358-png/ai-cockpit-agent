"""Vehicle-aware knowledge models and local registries."""

from .registry import DocumentRegistry, RegistryError, VehicleRegistry
from .schemas import (
    AnswerResult,
    DocumentMetadata,
    KnowledgeChunk,
    RetrievedChunk,
    VehicleProfile,
)

__all__ = [
    "AnswerResult",
    "DocumentMetadata",
    "DocumentRegistry",
    "KnowledgeChunk",
    "RegistryError",
    "RetrievedChunk",
    "VehicleProfile",
    "VehicleRegistry",
]
