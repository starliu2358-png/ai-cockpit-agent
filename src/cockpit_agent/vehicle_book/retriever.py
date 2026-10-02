from __future__ import annotations

import math
import re
from collections import Counter

from .ingest import KnowledgeIngestor
from .registry import RegistryError, VehicleRegistry
from .schemas import KnowledgeChunk, RetrievedChunk


class VehicleBookRetriever:
    """Vehicle-aware BM25 retrieval over registered local knowledge."""

    def __init__(
        self,
        vehicle_registry: VehicleRegistry | None = None,
        ingestor: KnowledgeIngestor | None = None,
    ) -> None:
        if ingestor is None:
            self.vehicle_registry = vehicle_registry or VehicleRegistry()
            self.ingestor = KnowledgeIngestor(vehicle_registry=self.vehicle_registry)
        else:
            self.ingestor = ingestor
            self.vehicle_registry = vehicle_registry or ingestor.vehicle_registry

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())

    @staticmethod
    def _bm25_score(
        query_tokens: list[str],
        document_tokens: list[str],
        document_frequency: Counter[str],
        document_count: int,
        average_length: float,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> float:
        term_frequency = Counter(document_tokens)
        score = 0.0

        for token in query_tokens:
            frequency = term_frequency[token]
            if frequency == 0:
                continue

            frequency_in_corpus = document_frequency[token]
            inverse_document_frequency = math.log(
                1
                + (document_count - frequency_in_corpus + 0.5)
                / (frequency_in_corpus + 0.5)
            )
            denominator = frequency + k1 * (
                1 - b + b * len(document_tokens) / max(average_length, 1)
            )
            score += inverse_document_frequency * (
                frequency * (k1 + 1)
            ) / denominator

        return score

    def retrieve(
        self,
        vehicle_id: str,
        query: str,
        top_k: int = 2,
        *,
        include_pre_release: bool = False,
    ) -> tuple[RetrievedChunk, ...]:
        """Resolve, authorize, load, and rank chunks for one exact vehicle."""
        profile = self.vehicle_registry.resolve(vehicle_id)

        if profile.release_status == "pre_release" and not include_pre_release:
            raise RegistryError(
                f"Vehicle '{profile.vehicle_id}' is pre_release; "
                "pass include_pre_release=True to retrieve its documents"
            )

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return ()

        loaded_chunks = self.ingestor.ingest(profile.vehicle_id)
        eligible_chunks = tuple(
            chunk
            for chunk in loaded_chunks
            if chunk.metadata.vehicle_id == profile.vehicle_id
            and chunk.metadata.status == "published"
        )
        if not eligible_chunks:
            return ()

        tokenized_chunks = [self._tokenize(chunk.text) for chunk in eligible_chunks]
        document_frequency: Counter[str] = Counter()
        for tokens in tokenized_chunks:
            document_frequency.update(set(tokens))

        document_count = len(tokenized_chunks)
        average_length = sum(map(len, tokenized_chunks)) / document_count
        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk, tokens in zip(eligible_chunks, tokenized_chunks, strict=True):
            score = self._bm25_score(
                query_tokens,
                tokens,
                document_frequency,
                document_count,
                average_length,
            )
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return tuple(
            RetrievedChunk(chunk=chunk, score=score, rank=rank)
            for rank, (score, chunk) in enumerate(scored[:top_k], start=1)
        )

    def search(
        self,
        vehicle_id: str,
        query: str,
        top_k: int = 2,
        *,
        include_pre_release: bool = False,
    ) -> tuple[RetrievedChunk, ...]:
        """Alias for retrieve, matching the legacy retriever's search terminology."""
        return self.retrieve(
            vehicle_id,
            query,
            top_k,
            include_pre_release=include_pre_release,
        )
