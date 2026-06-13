from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class Persona(BaseModel):
    id: str = Field(default_factory=_new_id)
    agent_id: str
    name: str
    description: str = ""
    traits: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class MemoryEntry(BaseModel):
    id: str = Field(default_factory=_new_id)
    persona_id: str
    key: str
    value: Any
    context: str = ""
    created_at: datetime = Field(default_factory=_utcnow)


class PersonaCreateRequest(BaseModel):
    agent_id: str
    name: str
    description: str = ""
    traits: dict[str, Any] = {}


class PersonaUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    traits: dict[str, Any] | None = None


class MemoryStoreRequest(BaseModel):
    key: str
    value: Any
    context: str = ""


class PersonaResponse(BaseModel):
    persona: Persona


class PersonaListResponse(BaseModel):
    personas: list[Persona]


class MemoryListResponse(BaseModel):
    memories: list[MemoryEntry]
