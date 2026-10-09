from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from cockpit_agent.api import FeedbackStore, create_app


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    return TestClient(
        create_app(feedback_store=FeedbackStore(tmp_path / "feedback.jsonl"))
    )


def test_lists_only_four_released_tesla_cn_trims(tmp_path: Path, monkeypatch) -> None:
    response = _client(tmp_path, monkeypatch).get("/api/v1/vehicles")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 4
    assert {item["trimId"] for item in payload} == {
        "model3-rwd-cn-current",
        "model3-lr-rwd-cn-current",
        "model3-lr-awd-cn-current",
        "model3-performance-awd-cn-current",
    }
    assert all(item["model"] == "Model 3" for item in payload)


def test_answers_charging_question_without_model_key(tmp_path: Path, monkeypatch) -> None:
    response = _client(tmp_path, monkeypatch).post(
        "/api/v1/answers",
        json={
            "question": "如何打开充电口？",
            "trimId": "model3-rwd-cn-current",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["boundaryResult"] is None
    assert payload["fallbackReason"] is None
    assert "打开充电端口" in payload["answer"]
    assert "切勿强行打开" in payload["answer"]
    assert payload["speechText"] == payload["answer"]
    assert payload["citations"] == [
        {
            "id": "tesla_model3_rwd_cn_charging_2024plus",
            "title": "Tesla 中国 Model 3 车主手册",
            "section": "打开充电端口",
            "url": "https://www.tesla.cn/ownersmanual/model3/zh_cn/"
            "GUID-BEE08D47-0CE0-4BDD-83F2-9854FB3D578F.html",
            "retrievedAt": "2026-10-09",
        }
    ]


def test_zero_retrieval_is_unconfirmed_not_unsupported(tmp_path: Path, monkeypatch) -> None:
    response = _client(tmp_path, monkeypatch).post(
        "/api/v1/answers",
        json={
            "question": "月球基地咖啡机怎么校准？",
            "trimId": "model3-rwd-cn-current",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallbackReason"] == "no_retrieval_results"
    assert payload["boundaryResult"] is None
    assert "足够可靠的依据" in payload["answer"]
    assert payload["citations"] == []


def test_rejects_market_and_software_fields(tmp_path: Path, monkeypatch) -> None:
    response = _client(tmp_path, monkeypatch).post(
        "/api/v1/answers",
        json={
            "question": "如何打开充电口？",
            "trimId": "model3-rwd-cn-current",
            "market": "US",
            "softwareVersion": "2026.1",
        },
    )

    assert response.status_code == 422


def test_rejects_unknown_trim(tmp_path: Path, monkeypatch) -> None:
    response = _client(tmp_path, monkeypatch).post(
        "/api/v1/answers",
        json={"question": "如何打开充电口？", "trimId": "model-y-us"},
    )

    assert response.status_code == 404


def test_feedback_is_idempotent_and_switchable(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    answer = client.post(
        "/api/v1/answers",
        json={
            "question": "如何打开充电口？",
            "trimId": "model3-rwd-cn-current",
        },
    ).json()
    endpoint = f"/api/v1/answers/{answer['answerId']}/feedback"

    first = client.post(endpoint, json={"value": "up"})
    repeated = client.post(endpoint, json={"value": "up"})
    switched = client.post(endpoint, json={"value": "down"})

    assert first.status_code == repeated.status_code == switched.status_code == 200
    assert first.json()["value"] == repeated.json()["value"] == "up"
    assert first.json()["recordedAt"] == repeated.json()["recordedAt"]
    assert switched.json()["value"] == "down"
    assert len((tmp_path / "feedback.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_feedback_rejects_unknown_answer(tmp_path: Path, monkeypatch) -> None:
    response = _client(tmp_path, monkeypatch).post(
        "/api/v1/answers/missing/feedback", json={"value": "up"}
    )

    assert response.status_code == 404
