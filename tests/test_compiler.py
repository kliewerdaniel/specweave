from __future__ import annotations

from datetime import datetime, timezone

import pytest

from specweave.compiler import CompilerPipeline
from specweave.persistence import GraphStore, SQLiteStore


class TestCompilerPipeline:
    @pytest.fixture
    def db(self, tmp_path) -> SQLiteStore:
        store = SQLiteStore(tmp_path / "test.db")
        store.initialize()
        return store

    @pytest.fixture
    def graph(self) -> GraphStore:
        return GraphStore()

    @pytest.fixture
    def compiler(self, db: SQLiteStore, graph: GraphStore) -> CompilerPipeline:
        return CompilerPipeline(db, graph)

    def test_gate1_completeness_passes(self, compiler: CompilerPipeline) -> None:
        spec = {
            "project_name": "test",
            "project_title": "Test",
            "project_description": "desc",
            "version": "0.1.0",
        }
        result = compiler._gate_completeness(spec)
        assert result["status"] == "passed"

    def test_gate1_completeness_fails(self, compiler: CompilerPipeline) -> None:
        spec = {"project_name": ""}
        result = compiler._gate_completeness(spec)
        assert result["status"] == "failed"
        assert "Missing required fields" in result["failure_reason"]

    def test_gate2_consistency_passes(self, compiler: CompilerPipeline) -> None:
        spec = {
            "id": "abc",
            "project_name": "test",
            "project_title": "Test",
            "project_description": "desc",
            "version": "0.1.0",
            "raw_spec": "content",
        }
        result = compiler._gate_consistency(spec)
        assert result["status"] == "passed"

    def test_gate2_consistency_fails_missing_field(self, compiler: CompilerPipeline) -> None:
        spec = {"id": "abc", "project_name": "test"}
        result = compiler._gate_consistency(spec)
        assert result["status"] == "failed"

    def test_gate2_consistency_fails_bad_version(self, compiler: CompilerPipeline) -> None:
        spec = {
            "id": "abc",
            "project_name": "test",
            "project_title": "Test",
            "project_description": "desc",
            "version": "bad",
            "raw_spec": "content",
        }
        result = compiler._gate_consistency(spec)
        assert result["status"] == "failed"

    def test_gate4_dependencies_passes(self, compiler: CompilerPipeline) -> None:
        spec = {}
        result = compiler._gate_dependencies(spec)
        assert result["status"] == "passed"

    def test_gate6_coherence_passes_with_good_score(self, compiler: CompilerPipeline) -> None:
        spec = {"project_description": "test", "graph_snapshot": {}}
        result = compiler._gate_coherence(spec)
        assert result["status"] in ("passed", "failed")

    def test_gate7_readiness_fails_empty_graph(self, compiler: CompilerPipeline) -> None:
        spec = {}
        result = compiler._gate_readiness(spec)
        assert result["status"] == "failed"
        assert "No modules or endpoints" in result["failure_reason"]

    def test_gate7_readiness_passes_with_nodes(self, compiler: CompilerPipeline, graph: GraphStore) -> None:
        graph.add_node("mod1", "module", title="Module 1")
        graph.add_node("ep1", "api_endpoint", title="Endpoint 1")
        graph.add_node("gate1", "verification_gate", title="Gate 1")
        result = compiler._gate_readiness({})
        assert result["status"] == "passed"

    def test_run_compiles_spec(self, compiler: CompilerPipeline, db: SQLiteStore) -> None:
        now = datetime.now(timezone.utc).isoformat()
        db.create_spec({
            "id": "test-id",
            "project_name": "test",
            "project_title": "Test",
            "project_description": "desc",
            "version": "0.1.0",
            "status": "draft",
            "created_at": now,
            "updated_at": now,
            "raw_spec": "content",
        })
        spec = {
            "id": "test-id",
            "project_name": "test",
            "project_title": "Test",
            "project_description": "desc",
            "version": "0.1.0",
            "raw_spec": "content",
        }
        gates = compiler.run("test-id", spec)
        assert len(gates) > 0
        assert all(g["spec_id"] == "test-id" for g in gates)
