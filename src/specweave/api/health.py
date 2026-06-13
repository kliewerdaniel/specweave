from fastapi import APIRouter

from specweave.models.spec import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/v2/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="2.0.0")
