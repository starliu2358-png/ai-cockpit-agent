from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from .vehicle_book.registry import REPOSITORY_ROOT, RegistryError, VehicleRegistry
from .vehicle_book.service import VehicleBookService

TESLA_CN_TRIM_IDS = (
    "model3-rwd-cn-current",
    "model3-lr-rwd-cn-current",
    "model3-lr-awd-cn-current",
    "model3-performance-awd-cn-current",
)
DEFAULT_FEEDBACK_PATH = REPOSITORY_ROOT / "outputs" / "feedback" / "cheshu_feedback.jsonl"


class VehicleOption(BaseModel):
    trimId: str
    displayName: str
    model: str


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    trimId: str = Field(min_length=1)


class CitationResponse(BaseModel):
    id: str
    title: str
    section: str
    url: str
    retrievedAt: str


class AnswerResponse(BaseModel):
    answerId: str
    answer: str
    boundaryResult: Literal["supported", "unsupported", "unconfirmed"] | None = None
    citations: list[CitationResponse]
    speechText: str
    fallbackReason: str | None = None


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Literal["up", "down"]


class FeedbackResponse(BaseModel):
    answerId: str
    value: Literal["up", "down"]
    recordedAt: str


class FeedbackStore:
    """Append local feedback events while keeping the latest value in memory."""

    def __init__(self, path: Path = DEFAULT_FEEDBACK_PATH) -> None:
        self.path = path
        self._lock = Lock()
        self._latest: dict[str, FeedbackResponse] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        if not self.path.is_file():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                event = FeedbackResponse.model_validate_json(line)
            except ValueError:
                continue
            self._latest[event.answerId] = event

    def record(self, answer_id: str, value: Literal["up", "down"]) -> FeedbackResponse:
        with self._lock:
            current = self._latest.get(answer_id)
            if current is not None and current.value == value:
                return current
            event = FeedbackResponse(
                answerId=answer_id,
                value=value,
                recordedAt=datetime.now(timezone.utc).isoformat(),
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
            self._latest[answer_id] = event
        return event


def create_app(
    *,
    service_factory: Callable[[], VehicleBookService] = VehicleBookService,
    vehicle_registry: VehicleRegistry | None = None,
    feedback_store: FeedbackStore | None = None,
) -> FastAPI:
    app = FastAPI(title="车书 AI API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    registry = vehicle_registry or VehicleRegistry()
    feedback = feedback_store or FeedbackStore()
    known_answers: set[str] = set()

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "market": "CN"}

    @app.get("/api/v1/vehicles", response_model=list[VehicleOption])
    def list_vehicles() -> list[VehicleOption]:
        options: list[VehicleOption] = []
        for trim_id in TESLA_CN_TRIM_IDS:
            profile = registry.resolve(trim_id)
            if profile.market != "CN" or profile.oem != "Tesla":
                continue
            options.append(
                VehicleOption(
                    trimId=profile.vehicle_id,
                    displayName=profile.display_name or profile.trim,
                    model=profile.model,
                )
            )
        return options

    @app.post("/api/v1/answers", response_model=AnswerResponse)
    def answer(request: AnswerRequest) -> AnswerResponse:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=422, detail="问题不能为空。")
        if request.trimId not in TESLA_CN_TRIM_IDS:
            raise HTTPException(status_code=404, detail="未找到该中国大陆车型配置。")
        try:
            profile = registry.resolve(request.trimId)
            if profile.market != "CN" or profile.oem != "Tesla":
                raise HTTPException(status_code=404, detail="未找到该中国大陆车型配置。")
            result = service_factory().answer(question, profile.vehicle_id)
        except RegistryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        answer_id = str(uuid4())
        known_answers.add(answer_id)
        citations = [
            CitationResponse(
                id=citation.document_id,
                title=citation.title,
                section=citation.section,
                url=citation.source_url or "",
                retrievedAt=citation.retrieved_at or "",
            )
            for citation in result.citations
            if citation.source_url
            and citation.market == "CN"
            and citation.source_url.startswith("https://www.tesla.cn/")
        ]
        return AnswerResponse(
            answerId=answer_id,
            answer=result.answer,
            citations=citations,
            speechText=result.answer,
            fallbackReason=result.fallback_reason,
        )

    @app.post(
        "/api/v1/answers/{answer_id}/feedback",
        response_model=FeedbackResponse,
    )
    def submit_feedback(answer_id: str, request: FeedbackRequest) -> FeedbackResponse:
        if answer_id not in known_answers:
            raise HTTPException(status_code=404, detail="未找到该回答。")
        return feedback.record(answer_id, request.value)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("cockpit_agent.api:app", host="127.0.0.1", port=8000, reload=True)
