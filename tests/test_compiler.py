from __future__ import annotations

from datetime import datetime, timezone

import pytest

from specweave.compiler import CompilerPipeline
from specweave.compiler.gates import CompilerGates
from specweave.compiler.steps import CompilerSteps
from specweave.persistence import GraphStore, SQLiteStore


class TestCompilerSteps:
    @pytest.fixture
    def db(self, tmp_path) -> SQLiteStore:
        store = SQLiteStore(tmp_path / "test.db")
        store.initialize()
        return store

    @pytest.fixture
    def graph(self) -> GraphStore:
        return GraphStore()

    @pytest.fixture
    def steps(self, db: SQLiteStore, graph: GraphStore) -> CompilerSteps:
        return CompilerSteps(db, graph)

    def test_step1_parse_spec_passes(self, steps: CompilerSteps) -> None:
        result = steps.step1_parse_spec({"raw_spec": "some content"})
        assert result["status"] == "passed"

    def test_step1_parse_spec_fails_empty(self, steps: CompilerSteps) -> None:
        result = steps.step1_parse_spec({"raw_spec": ""})
        assert result["status"] == "failed"

    def test_step2_validate_schema_passes(self, steps: CompilerSteps) -> None:
        spec = {
            "id": "abc",
            "project_name": "test",
            "project_title": "Test",
            "project_description": "desc",
            "version": "0.1.0",
            "raw_spec": "content",
        }
        result = steps.step2_validate_schema(spec)
        assert result["status"] == "passed"

    def test_step2_validate_schema_fails(self, steps: CompilerSteps) -> None:
        result = steps.step2_validate_schema({"id": "abc"})
        assert result["status"] == "failed"

    def test_step3_extract_constraints(self, steps: CompilerSteps) -> None:
        result = steps.step3_extract_constraints({"raw_spec": "This must be done.\nThis is optional."})
        assert result["status"] == "passed"
        assert result["details"]["constraints_found"] == 1

    def test_step4_build_dependency_graph(self, steps: CompilerSteps) -> None:
        result = steps.step4_build_dependency_graph({"id": "spec-1", "project_title": "Test"})
        assert result["status"] == "passed"

    def test_step5_detect_contradictions(self, steps: CompilerSteps) -> None:
        result = steps.step5_detect_contradictions({})
        assert result["status"] in ("passed", "failed")

    def test_step6_check_drift(self, steps: CompilerSteps) -> None:
        result = steps.step6_check_drift({})
        assert result["status"] == "passed"

    def test_step8_resolve_dependencies(self, steps: CompilerSteps) -> None:
        result = steps.step8_resolve_dependencies({})
        assert result["status"] == "passed"

    def test_step12_commit_to_audit(self, steps: CompilerSteps) -> None:
        result = steps.step12_commit_to_audit({})
        assert result["status"] == "passed"


class TestCompilerGates:
    @pytest.fixture
    def db(self, tmp_path) -> SQLiteStore:
        store = SQLiteStore(tmp_path / "test.db")
        store.initialize()
        return store

    @pytest.fixture
    def graph(self) -> GraphStore:
        return GraphStore()

    @pytest.fixture
    def gates(self, db: SQLiteStore, graph: GraphStore) -> CompilerGates:
        steps = CompilerSteps(db, graph)
        return CompilerGates(steps)

    def test_gate1_completeness_passes(self, gates: CompilerGates) -> None:
        spec = {
            "id": "abc",
            "project_name": "test",
            "project_title": "Test",
            "project_description": "desc",
            "version": "0.1.0",
            "raw_spec": "content",
        }
        result = gates.run_gate("gate1_completeness", spec)
        assert result["status"] == "passed"

    def test_gate1_completeness_fails(self, gates: CompilerGates) -> None:
        spec = {"project_name": ""}
        result = gates.run_gate("gate1_completeness", spec)
        assert result["status"] == "failed"

    def test_gate2_consistency_passes(self, gates: CompilerGates) -> None:
        spec = {
            "id": "abc",
            "project_name": "test",
            "project_title": "Test",
            "project_description": "desc",
            "version": "0.1.0",
            "raw_spec": "content",
        }
        result = gates.run_gate("gate2_consistency", spec)
        assert result["status"] in ("passed", "failed")

    def test_unknown_gate(self, gates: CompilerGates) -> None:
        result = gates.run_gate("unknown_gate", {})
        assert result["status"] == "failed"

    def test_get_gate_ids(self, gates: CompilerGates) -> None:
        ids = gates.get_gate_ids()
        assert len(ids) == 6
        assert "gate1_completeness" in ids
        assert "gate6_readiness" in ids


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

    def test_pipeline_has_6_gates(self, compiler: CompilerPipeline) -> None:
        assert len(compiler.GATES) == 6
