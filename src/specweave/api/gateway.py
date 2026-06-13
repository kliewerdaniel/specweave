from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from specweave.auth import get_current_user
from specweave.gateway import A2AHandler, MCPHandler
from specweave.models.spec import (
    A2ADelegationRequest,
    A2ADelegationResponse,
    A2ASpecListResponse,
    A2ASubmissionRequest,
    A2ASubmissionResponse,
    MCPExecuteRequest,
    MCPExecuteResponse,
    MCPToolListResponse,
)
from specweave.persistence import SQLiteStore

router = APIRouter(prefix="/api/v2", tags=["gateway"])


async def _get_db(request: Request) -> SQLiteStore:
    return request.app.state.db


def _get_a2a(db: SQLiteStore) -> A2AHandler:
    return A2AHandler(db)


def _get_mcp(db: SQLiteStore) -> MCPHandler:
    return MCPHandler(db)


@router.get("/a2a/specs", response_model=A2ASpecListResponse)
async def a2a_discover(
    user: str = Depends(get_current_user),
    db: SQLiteStore = Depends(_get_db),
) -> A2ASpecListResponse:
    specs = _get_a2a(db).discover_specs()
    return A2ASpecListResponse(specs=specs)


@router.post("/a2a/delegate", response_model=A2ADelegationResponse)
async def a2a_delegate(
    req: A2ADelegationRequest,
    user: str = Depends(get_current_user),
    db: SQLiteStore = Depends(_get_db),
) -> A2ADelegationResponse:
    delegation = _get_a2a(db).delegate(req.spec_id, req.sub_spec_content, req.target_agent)
    return A2ADelegationResponse(delegation_id=delegation["id"], status=delegation["status"])


@router.post("/a2a/submit", response_model=A2ASubmissionResponse)
async def a2a_submit(
    req: A2ASubmissionRequest,
    user: str = Depends(get_current_user),
    db: SQLiteStore = Depends(_get_db),
) -> A2ASubmissionResponse:
    result = _get_a2a(db).submit(req.delegation_id, req.result)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delegation not found")
    return A2ASubmissionResponse(delegation_id=req.delegation_id, status=result["status"])


@router.get("/mcp/tools", response_model=MCPToolListResponse)
async def mcp_tools(
    user: str = Depends(get_current_user),
    db: SQLiteStore = Depends(_get_db),
) -> MCPToolListResponse:
    tools = _get_mcp(db).list_tools()
    return MCPToolListResponse(tools=tools)


@router.post("/mcp/execute", response_model=MCPExecuteResponse)
async def mcp_execute(
    req: MCPExecuteRequest,
    user: str = Depends(get_current_user),
    db: SQLiteStore = Depends(_get_db),
) -> MCPExecuteResponse:
    try:
        result = _get_mcp(db).execute(req.tool, req.params)
        return MCPExecuteResponse(result=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
