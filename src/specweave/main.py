from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from specweave.api import gateway_router, health_router, specs_router
from specweave.config import settings
from specweave.persistence import GraphStore, SQLiteStore, VectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SQLiteStore(settings.sqlite_path)
    db.initialize()

    vector_store = VectorStore(settings.chroma_path)

    graph_store = GraphStore()
    graph_store.add_node("specweave", "spec_section", title="SpecWeave", status="active")
    graph_store.add_node("persistence", "module", title="Persistence Layer")
    graph_store.add_node("neuro_symbolic", "module", title="Neuro-Symbolic KG")
    graph_store.add_node("speculative", "module", title="Speculative Engine")
    graph_store.add_node("compiler", "module", title="Self-Verifying Compiler")
    graph_store.add_node("gateway", "module", title="A2A/MCP Gateway")

    graph_store.add_edge("specweave", "persistence", "depends_on")
    graph_store.add_edge("specweave", "neuro_symbolic", "depends_on")
    graph_store.add_edge("specweave", "speculative", "depends_on")
    graph_store.add_edge("specweave", "compiler", "depends_on")
    graph_store.add_edge("specweave", "gateway", "depends_on")
    graph_store.add_edge("neuro_symbolic", "persistence", "depends_on")
    graph_store.add_edge("speculative", "neuro_symbolic", "depends_on")
    graph_store.add_edge("compiler", "neuro_symbolic", "depends_on")
    graph_store.add_edge("compiler", "speculative", "depends_on")
    graph_store.add_edge("gateway", "persistence", "depends_on")
    graph_store.add_edge("gateway", "neuro_symbolic", "depends_on")

    app.state.db = db
    app.state.vector_store = vector_store
    app.state.graph_store = graph_store
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

cors_allowed = [s.strip() for s in settings.cors_origins.split(",") if s.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed if cors_allowed else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(specs_router)
app.include_router(gateway_router)
