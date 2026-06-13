from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from specweave import main as app_module
from specweave.config import settings
from specweave.main import app as real_app
from specweave.persistence import GraphStore, SQLiteStore, VectorStore


@pytest.fixture(autouse=True)
def patch_settings(tmp_path: Path) -> None:
    settings.sqlite_path = tmp_path / "test.db"
    settings.chroma_path = str(tmp_path / "chroma")
    settings.data_dir = tmp_path / ".sovereignspec"
    agents_dir = settings.data_dir / "agents" / "test-agent"
    agents_dir.mkdir(parents=True, exist_ok=True)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    db = SQLiteStore(settings.sqlite_path)
    db.initialize()
    vector_store = VectorStore(settings.chroma_path)
    graph_store = GraphStore()

    real_app.state.db = db
    real_app.state.vector_store = vector_store
    real_app.state.graph_store = graph_store

    transport = ASGITransport(app=real_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_db(tmp_path: Path) -> SQLiteStore:
    db_path = tmp_path / "test.db"
    store = SQLiteStore(db_path)
    store.initialize()
    return store


@pytest.fixture
def graph() -> GraphStore:
    return GraphStore()


@pytest.fixture
def vector_store(tmp_path: Path) -> VectorStore:
    return VectorStore(str(tmp_path / "chroma"))


@pytest.fixture
def mock_ollama_client() -> MagicMock:
    mock = MagicMock()
    mock.generate.return_value.response = '{"key": "value"}'
    return mock


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-Agent-Id": "test-agent"}
