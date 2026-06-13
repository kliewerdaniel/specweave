from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class Contradiction(BaseModel):
    id: str = Field(default_factory=_new_id)
    spec_id: str
    section_a: str
    section_b: str
    description: str
    severity: str = "medium"
    detected_at: datetime = Field(default_factory=_utcnow)


class Drift(BaseModel):
    id: str = Field(default_factory=_new_id)
    spec_id: str
    field: str
    baseline_value: Any = None
    current_value: Any = None
    drift_score: float = 0.0
    detected_at: datetime = Field(default_factory=_utcnow)


class ContradictionDetectionResponse(BaseModel):
    spec_id: str
    contradictions: list[Contradiction]
    count: int


class DriftDetectionResponse(BaseModel):
    spec_id: str
    drifts: list[Drift]
    count: int
