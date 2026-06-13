import tempfile
from pathlib import Path

import pytest

from specweave.persistence.sqlite_store import SQLiteStore
from specweave.persistence.graph_store import GraphStore


@pytest.fixture
def db():
    with tempfile.TemporaryDirectory() as tmp:
        store = SQLiteStore(Path(tmp) / "test.db")
        store.initialize()
        yield store


@pytest.fixture
def graph():
    return GraphStore()


class TestSQLiteStore:
    def test_initialize_creates_tables(self, db):
        with db._connect() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {t["name"] for t in tables}
            assert "specs" in table_names
            assert "verification_gates" in table_names
            assert "speculations" in table_names
            assert "delegations" in table_names
            assert "audit_records" in table_names

    def test_create_and_get_spec(self, db):
        spec = {
            "id": "spec-1",
            "project_name": "test",
            "project_title": "Test Spec",
            "project_description": "A test",
            "version": "1.0.0",
            "status": "draft",
            "raw_spec": "content",
        }
        created = db.create_spec(spec)
        assert created["id"] == "spec-1"

        fetched = db.get_spec("spec-1")
        assert fetched is not None
        assert fetched["project_title"] == "Test Spec"

    def test_list_specs(self, db):
        db.create_spec({"id": "s1", "project_name": "a", "project_title": "A", "project_description": "d"})
        db.create_spec({"id": "s2", "project_name": "b", "project_title": "B", "project_description": "d"})
        specs = db.list_specs()
        assert len(specs) == 2

    def test_update_spec(self, db):
        db.create_spec({"id": "s1", "project_name": "a", "project_title": "A", "project_description": "d"})
        updated = db.update_spec("s1", {"status": "compiled"})
        assert updated["status"] == "compiled"

    def test_delete_spec(self, db):
        db.create_spec({"id": "s1", "project_name": "a", "project_title": "A", "project_description": "d"})
        assert db.delete_spec("s1") is True
        assert db.get_spec("s1") is None

    def test_create_and_get_gate(self, db):
        db.create_spec({"id": "s1", "project_name": "a", "project_title": "A", "project_description": "d"})
        gate = db.create_gate({
            "id": "g1", "spec_id": "s1", "gate_id": "gate1",
            "status": "passed", "checked_at": "2024-01-01T00:00:00",
        })
        assert gate["status"] == "passed"

        gates = db.get_gates_for_spec("s1")
        assert len(gates) == 1

    def test_audit_trail(self, db):
        db.create_spec({"id": "s1", "project_name": "a", "project_title": "A", "project_description": "d"})
        db.create_audit_record({
            "id": "a1", "spec_id": "s1", "action": "test", "actor": "user",
            "details": {"key": "val"}, "created_at": "2024-01-01T00:00:00",
        })
        records = db.get_audit_for_spec("s1")
        assert len(records) == 1
        assert records[0]["action"] == "test"


class TestGraphStore:
    def test_add_node(self, graph):
        graph.add_node("test-node", "module", description="test")
        assert graph.has_node("test-node")
        node = graph.get_node("test-node")
        assert node["type"] == "module"

    def test_invalid_node_type(self, graph):
        with pytest.raises(ValueError):
            graph.add_node("bad", "invalid_type")

    def test_add_edge(self, graph):
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_edge("a", "b", "depends_on")
        assert graph.has_edge("a", "b")

    def test_invalid_edge_type(self, graph):
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        with pytest.raises(ValueError):
            graph.add_edge("a", "b", "invalid_edge")

    def test_cycle_detection(self, graph):
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_node("c", "module")
        graph.add_edge("a", "b", "depends_on")
        graph.add_edge("b", "c", "depends_on")
        graph.add_edge("c", "a", "depends_on")
        assert graph.has_cycle()
        assert len(graph.find_cycle_path()) > 0

    def test_no_cycle(self, graph):
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_edge("a", "b", "depends_on")
        assert not graph.has_cycle()

    def test_get_neighbors(self, graph):
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_edge("a", "b", "depends_on")
        neighbors = graph.get_neighbors("a")
        assert len(neighbors) == 1
        assert neighbors[0]["target"] == "b"

    def test_get_nodes_by_type(self, graph):
        graph.add_node("ep1", "api_endpoint")
        graph.add_node("ep2", "api_endpoint")
        graph.add_node("mod1", "module")
        eps = graph.get_nodes_by_type("api_endpoint")
        assert len(eps) == 2

    def test_adjacency(self, graph):
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_edge("a", "b", "depends_on")
        adj = graph.get_adjacency()
        assert "a" in adj
        assert "b" in adj["a"]

    def test_to_json(self, graph):
        graph.add_node("a", "module", title="A")
        graph.add_node("b", "module", title="B")
        graph.add_edge("a", "b", "depends_on")
        data = graph.to_json()
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
