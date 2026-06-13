from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from specweave.auth import get_current_user
from specweave.compiler import CompilerPipeline
from specweave.gateway import A2AHandler
from specweave.models.spec import (
    A2ADelegationResponse,
    A2ASpecListResponse,
    A2ASubmissionRequest,
    A2ASubmissionResponse,
    AuditRecord,
    AuditTrailResponse,
    CompilationResponse,
    Delegation,
    DelegationListResponse,
    DelegationRequest,
    DelegationResponse,
    GateStatusResponse,
    GraphResponse,
    MCPExecuteRequest,
    MCPExecuteResponse,
    MCPToolListResponse,
    Spec,
    SpecCreateRequest,
    SpecDetailResponse,
    SpecListResponse,
    SpecResponse,
    SpeculateRequest,
    Speculation,
    SpeculationResponse,
    VerificationGate,
    VerificationResponse,
)
from specweave.neuro_symbolic import NeuralChecker, SymbolicValidator
from specweave.persistence import GraphStore, SQLiteStore, VectorStore
from specweave.config import settings
from specweave.speculative import SpeculativeEngine

router = APIRouter(prefix="/api/v2", tags=["specs"])

_db_instance: SQLiteStore | None = None
_vector_store_instance: VectorStore | None = None
graph_store = GraphStore()


def _get_db() -> SQLiteStore:
    global _db_instance
    if _db_instance is None:
        _db_instance = SQLiteStore(settings.sqlite_path)
        _db_instance.initialize()
    return _db_instance


def _get_vector_store() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(settings.chroma_path)
    return _vector_store_instance


def _get_compiler() -> CompilerPipeline:
    return CompilerPipeline(_get_db(), graph_store)


def _get_speculative() -> SpeculativeEngine:
    return SpeculativeEngine()


def _get_neural() -> NeuralChecker:
    return NeuralChecker()


def _get_a2a() -> A2AHandler:
    return A2AHandler(_get_db())


def _build_spec_from_request(req: SpecCreateRequest) -> Spec:
    now = datetime.now(timezone.utc).isoformat()
    spec_id = str(uuid4())
    return Spec(
        id=spec_id,
        project_name=req.project_name,
        project_title=req.project_title,
        project_description=req.project_description,
        version=req.version,
        status="draft",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        raw_spec=req.raw_spec,
    )


@router.get("/specs", response_model=SpecListResponse)
async def list_specs(user: str = Depends(get_current_user)) -> SpecListResponse:
    specs_data = _get_db().list_specs()
    specs = [Spec(**s) for s in specs_data]
    return SpecListResponse(specs=specs)


@router.post("/specs", response_model=SpecResponse, status_code=status.HTTP_201_CREATED)
async def create_spec(req: SpecCreateRequest, user: str = Depends(get_current_user)) -> SpecResponse:
    spec = _build_spec_from_request(req)
    spec_dict = spec.model_dump()
    spec_dict["created_at"] = spec.created_at.isoformat()
    spec_dict["updated_at"] = spec.updated_at.isoformat()
    created = _get_db().create_spec(spec_dict)

    graph_store.add_node(
        spec.id,
        node_type="spec_section",
        title=spec.project_title,
        status=spec.status,
    )

    _get_db().create_audit_record({
        "id": str(uuid4()),
        "spec_id": spec.id,
        "action": "create",
        "actor": user,
        "details": {"title": spec.project_title},
        "created_at": spec.created_at.isoformat(),
    })

    return SpecResponse(spec=Spec(**created))


@router.get("/specs/{spec_id}", response_model=SpecDetailResponse)
async def get_spec(spec_id: str, user: str = Depends(get_current_user)) -> SpecDetailResponse:
    spec_data = _get_db().get_spec(spec_id)
    if spec_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found")
    graph_json = graph_store.to_json()
    gates = _get_db().get_gates_for_spec(spec_id)
    return SpecDetailResponse(
        spec=Spec(**spec_data),
        graph=graph_json,
        verification={"gates": gates},
    )


@router.post("/specs/{spec_id}/compile", response_model=CompilationResponse)
async def compile_spec(spec_id: str, user: str = Depends(get_current_user)) -> CompilationResponse:
    spec_data = _get_db().get_spec(spec_id)
    if spec_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found")

    compiler = _get_compiler()
    gates = compiler.run(spec_id, spec_data)
    status_str = "compiled" if all(g["status"] == "passed" for g in gates) else "failed"

    return CompilationResponse(
        spec_id=spec_id,
        gates=[VerificationGate(**g) for g in gates],
        status=status_str,
    )


@router.post("/specs/{spec_id}/speculate", response_model=SpeculationResponse)
async def speculate_spec(
    spec_id: str, req: SpeculateRequest, user: str = Depends(get_current_user)
) -> SpeculationResponse:
    spec_data = _get_db().get_spec(spec_id)
    if spec_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found")

    engine = _get_speculative()
    constraints = ["local-first", "no-cloud", "governed"]
    candidates = engine.speculate(
        spec_id=spec_id,
        section_id=req.section_id,
        section_content=spec_data.get("raw_spec", ""),
        constraints=constraints,
    )

    for c in candidates:
        _get_db().create_speculation(c)

    return SpeculationResponse(candidates=[Speculation(**c) for c in candidates])


@router.post("/specs/{spec_id}/verify", response_model=VerificationResponse)
async def verify_spec(spec_id: str, user: str = Depends(get_current_user)) -> VerificationResponse:
    spec_data = _get_db().get_spec(spec_id)
    if spec_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found")

    symbolic = SymbolicValidator(graph_store)
    symbolic_results = symbolic.check_all()
    all_passed = all(r["passed"] for r in symbolic_results)

    neural = _get_neural()
    neural_result = neural.architectural_coherence_check(str(spec_data))

    gates = _get_db().get_gates_for_spec(spec_id)

    _get_db().create_audit_record({
        "id": str(uuid4()),
        "spec_id": spec_id,
        "action": "verify",
        "actor": user,
        "details": {"symbolic_results": symbolic_results, "neural_result": neural_result},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return VerificationResponse(
        spec_id=spec_id,
        gates=[VerificationGate(**g) for g in gates],
        passed=all_passed,
    )


@router.get("/specs/{spec_id}/gates", response_model=GateStatusResponse)
async def get_gates(spec_id: str, user: str = Depends(get_current_user)) -> GateStatusResponse:
    gates = _get_db().get_gates_for_spec(spec_id)
    return GateStatusResponse(gates=[VerificationGate(**g) for g in gates])


@router.get("/specs/{spec_id}/delegates", response_model=DelegationListResponse)
async def list_delegations(spec_id: str, user: str = Depends(get_current_user)) -> DelegationListResponse:
    delegations = _get_db().get_delegations_for_spec(spec_id)
    return DelegationListResponse(delegations=[Delegation(**d) for d in delegations])


@router.post("/specs/{spec_id}/delegates", response_model=DelegationResponse)
async def create_delegation(
    spec_id: str, req: DelegationRequest, user: str = Depends(get_current_user)
) -> DelegationResponse:
    a2a = _get_a2a()
    delegation = a2a.delegate(spec_id, req.sub_spec_content, req.target_agent)
    return DelegationResponse(delegation=Delegation(**delegation))


@router.get("/specs/{spec_id}/graph", response_model=GraphResponse)
async def get_graph(spec_id: str, user: str = Depends(get_current_user)) -> GraphResponse:
    if not graph_store.has_node(spec_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found in graph")
    adj = graph_store.get_adjacency()
    return GraphResponse(adjacency=adj)


@router.get("/specs/{spec_id}/audit", response_model=AuditTrailResponse)
async def get_audit_trail(spec_id: str, user: str = Depends(get_current_user)) -> AuditTrailResponse:
    records = _get_db().get_audit_for_spec(spec_id)
    return AuditTrailResponse(records=[AuditRecord(**r) for r in records])
