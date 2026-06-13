from specweave.api.specs import router as specs_router
from specweave.api.gateway import router as gateway_router
from specweave.api.health import router as health_router

__all__ = ["specs_router", "gateway_router", "health_router"]
