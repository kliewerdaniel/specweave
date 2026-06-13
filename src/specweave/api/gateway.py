from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from specweave.auth import get_current_user
from specweave.config import settings
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

_a2a_instance: A2AHandler | None = None
_mcp_instance: MCPHandler | None = None


def _get_a2a() -> A2AHandler:
    global _a2a_instance
    if _a2a_instance is None:
        db = SQLiteStore(settings.sqlite_path)
        db.initialize()
        _a2a_instance = A2AHandler(db)
    return _a2a_instance


def _get_mcp() -> MCPHandler:
    global _mcp_instance
    if _mcp_instance is None:
        db = SQLiteStore(settings.sqlite_path)
        db.initialize()
        _mcp_instance = MCPHandler(db)
    return _mcp_instance


@router.get("/a2a/specs", response_model=A2ASpecListResponse)
async def a2a_discover(user: str = Depends(get_current_user)) -> A2ASpecListResponse:
    specs = _get_a2a().discover_specs()
    return A2ASpecListResponse(specs=specs)


@router.post("/a2a/delegate", response_model=A2ADelegationResponse)
async def a2a_delegate(
    req: A2ADelegationRequest, user: str = Depends(get_current_user)
) -> A2ADelegationResponse:
    delegation = _get_a2a().delegate(req.spec_id, req.sub_spec_content, req.target_agent)
    return A2ADelegationResponse(delegation_id=delegation["id"], status=delegation["status"])


@router.post("/a2a/submit", response_model=A2ASubmissionResponse)
async def a2a_submit(
    req: A2ASubmissionRequest, user: str = Depends(get_current_user)
) -> A2ASubmissionResponse:
    result = _get_a2a().submit(req.delegation_id, req.result)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delegation not found")
    return A2ASubmissionResponse(delegation_id=req.delegation_id, status=result["status"])


@router.get("/mcp/tools", response_model=MCPToolListResponse)
async def mcp_tools(user: str = Depends(get_current_user)) -> MCPToolListResponse:
    tools = _get_mcp().list_tools()
    return MCPToolListResponse(tools=tools)


@router.post("/mcp/execute", response_model=MCPExecuteResponse)
async def mcp_execute(
    req: MCPExecuteRequest, user: str = Depends(get_current_user)
) -> MCPExecuteResponse:
    try:
        result = _get_mcp().execute(req.tool, req.params)
        return MCPExecuteResponse(result=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
