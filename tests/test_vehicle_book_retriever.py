from pathlib import Path

import pytest

from cockpit_agent.vehicle_book.registry import RegistryError
from cockpit_agent.vehicle_book.retriever import VehicleBookRetriever
from cockpit_agent.vehicle_book.schemas import RetrievedChunk


@pytest.mark.parametrize(
    ("vehicle_id", "expected_document_prefix"),
    [
        ("alpha_aster_x1_max_v1", "oem_alpha_aster_x1_v1_"),
        ("alpha_aster_x2_max_v1", "oem_alpha_aster_x2_v1_"),
    ],
)
def test_released_profiles_retrieve_only_exact_vehicle_chunks(
    vehicle_id: str, expected_document_prefix: str
) -> None:
    results = VehicleBookRetriever().retrieve(
        vehicle_id, "battery charging HVAC LCC seat", top_k=20
    )

    assert results
    assert all(isinstance(result, RetrievedChunk) for result in results)
    assert all(result.chunk.metadata.vehicle_id == vehicle_id for result in results)
    assert all(
        result.chunk.metadata.document_id.startswith(expected_document_prefix)
        for result in results
    )
    assert all(result.chunk.metadata.status == "published" for result in results)
    assert all(
        isinstance(result.chunk.metadata.source_path, Path)
        and not result.chunk.metadata.source_path.is_absolute()
        for result in results
    )
    assert [result.rank for result in results] == list(range(1, len(results) + 1))
    assert all(result.score > 0 for result in results)


def test_pre_release_profile_requires_explicit_opt_in() -> None:
    retriever = VehicleBookRetriever()

    with pytest.raises(RegistryError, match="include_pre_release=True"):
        retriever.retrieve("alpha_aster_x1_max_v2", "HPA")

    results = retriever.retrieve(
        "alpha_aster_x1_max_v2",
        "HPA memorized route",
        include_pre_release=True,
    )

    assert results
    assert {
        result.chunk.metadata.vehicle_id for result in results
    } == {"alpha_aster_x1_max_v2"}
    assert all(
        result.chunk.metadata.document_id.startswith("oem_alpha_aster_x1_v2_")
        for result in results
    )


def test_unknown_vehicle_fails_with_registry_error() -> None:
    with pytest.raises(RegistryError, match="Unknown vehicle_id 'missing_vehicle'"):
        VehicleBookRetriever().retrieve("missing_vehicle", "ACC")


@pytest.mark.parametrize("top_k", [0, -1])
def test_top_k_must_be_positive(top_k: int) -> None:
    with pytest.raises(ValueError, match="top_k must be positive"):
        VehicleBookRetriever().retrieve(
            "alpha_aster_x1_max_v1", "ACC", top_k=top_k
        )


def test_blank_query_returns_no_results() -> None:
    assert VehicleBookRetriever().retrieve(
        "alpha_aster_x1_max_v1", "  \n\t"
    ) == ()
