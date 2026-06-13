from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class DelegationStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    timeout = "timeout"


class Spec(BaseModel):
    id: str
    project_name: str
    project_title: str
    project_description: str
    version: str = "0.1.0"
    status: str = "draft"
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    raw_spec: str = ""
    graph_snapshot: dict[str, Any] | None = None
    verification_report: dict[str, Any] | None = None


class VerificationGate(BaseModel):
    id: str = Field(default_factory=_new_id)
    spec_id: str
    gate_id: str
    status: str = "pending"
    failure_reason: str | None = None
    failure_location: dict[str, Any] | None = None
    checked_at: datetime | None = None


class Speculation(BaseModel):
    id: str = Field(default_factory=_new_id)
    spec_id: str
    section_id: str
    candidate_index: int
    architecture_description: str
    constraint_scores: dict[str, float] | None = None
    status: str = "drafted"
    rejection_reason: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class Delegation(BaseModel):
    id: str = Field(default_factory=_new_id)
    spec_id: str
    sub_spec_content: str
    target_agent: str
    status: DelegationStatus = DelegationStatus.pending
    result: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    ttl_seconds: int = 3600

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.created_at + timedelta(seconds=self.ttl_seconds)


class AuditRecord(BaseModel):
    id: str = Field(default_factory=_new_id)
    spec_id: str
    action: str
    actor: str
    details: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class SpecCreateRequest(BaseModel):
    project_name: str
    project_title: str
    project_description: str
    version: str = "0.1.0"
    raw_spec: str


class SpeculateRequest(BaseModel):
    section_id: str


class DelegationRequest(BaseModel):
    sub_spec_content: str
    target_agent: str


class A2ADelegationRequest(BaseModel):
    spec_id: str
    sub_spec_content: str
    target_agent: str


class A2ASubmissionRequest(BaseModel):
    delegation_id: str
    result: str


class MCPExecuteRequest(BaseModel):
    tool: str
    params: dict[str, Any] = {}


class SpecListResponse(BaseModel):
    specs: list[Spec]


class SpecResponse(BaseModel):
    spec: Spec


class SpecDetailResponse(BaseModel):
    spec: Spec
    graph: dict[str, Any] | None = None
    verification: dict[str, Any] | None = None


class CompilationResponse(BaseModel):
    spec_id: str
    gates: list[VerificationGate]
    status: str


class SpeculationResponse(BaseModel):
    candidates: list[Speculation]


class VerificationResponse(BaseModel):
    spec_id: str
    gates: list[VerificationGate]
    passed: bool


class GateStatusResponse(BaseModel):
    gates: list[VerificationGate]


class DelegationListResponse(BaseModel):
    delegations: list[Delegation]


class DelegationResponse(BaseModel):
    delegation: Delegation


class GraphResponse(BaseModel):
    adjacency: dict[str, list[str]]


class AuditTrailResponse(BaseModel):
    records: list[AuditRecord]


class A2ASpecListResponse(BaseModel):
    specs: list[dict[str, str]]


class A2ADelegationResponse(BaseModel):
    delegation_id: str
    status: str


class A2ASubmissionResponse(BaseModel):
    delegation_id: str
    status: str


class MCPTool(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = {}


class MCPToolListResponse(BaseModel):
    tools: list[MCPTool]


class MCPExecuteResponse(BaseModel):
    result: Any


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"
