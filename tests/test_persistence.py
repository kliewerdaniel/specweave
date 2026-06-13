from __future__ import annotations

from datetime import datetime, timezone

import pytest

from specweave.persistence.graph_store import GraphStore
from specweave.persistence.sqlite_store import SQLiteStore
from specweave.persistence.vector_store import VectorStore


class TestSQLiteStore:
    @pytest.fixture
    def store(self, tmp_path) -> SQLiteStore:
        s = SQLiteStore(tmp_path / "test.db")
        s.initialize()
        return s

    def test_create_and_get_spec(self, store: SQLiteStore) -> None:
        now = datetime.now(timezone.utc).isoformat()
        spec = {
            "id": "s1", "project_name": "p", "project_title": "P",
            "project_description": "d", "version": "0.1.0",
            "status": "draft", "created_at": now, "updated_at": now,
        }
        created = store.create_spec(spec)
        assert created["id"] == "s1"

        fetched = store.get_spec("s1")
        assert fetched is not None
        assert fetched["project_name"] == "p"

    def test_list_specs_empty(self, store: SQLiteStore) -> None:
        assert store.list_specs() == []

    def test_list_specs_with_data(self, store: SQLiteStore) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for i in range(3):
            store.create_spec({
                "id": f"s{i}", "project_name": f"p{i}", "project_title": f"P{i}",
                "project_description": "d", "version": "0.1.0",
                "status": "draft", "created_at": now, "updated_at": now,
            })
        specs = store.list_specs()
        assert len(specs) == 3

    def test_update_spec(self, store: SQLiteStore) -> None:
        now = datetime.now(timezone.utc).isoformat()
        store.create_spec({
            "id": "s1", "project_name": "p", "project_title": "P",
            "project_description": "d", "version": "0.1.0",
            "status": "draft", "created_at": now, "updated_at": now,
        })
        updated = store.update_spec("s1", {"status": "active"})
        assert updated is not None
        assert updated["status"] == "active"

    def test_delete_spec(self, store: SQLiteStore) -> None:
        now = datetime.now(timezone.utc).isoformat()
        store.create_spec({
            "id": "s1", "project_name": "p", "project_title": "P",
            "project_description": "d", "version": "0.1.0",
            "status": "draft", "created_at": now, "updated_at": now,
        })
        assert store.delete_spec("s1") is True
        assert store.get_spec("s1") is None

    def test_gate_crud(self, store: SQLiteStore) -> None:
        now = datetime.now(timezone.utc).isoformat()
        store.create_spec({
            "id": "s1", "project_name": "p", "project_title": "P",
            "project_description": "d", "version": "0.1.0",
            "status": "draft", "created_at": now, "updated_at": now,
        })
        gate = {
            "id": "g1", "spec_id": "s1", "gate_id": "gate1",
            "status": "passed", "checked_at": now,
        }
        store.create_gate(gate)
        gates = store.get_gates_for_spec("s1")
        assert len(gates) == 1

    def test_delegation_crud(self, store: SQLiteStore) -> None:
        now = datetime.now(timezone.utc).isoformat()
        store.create_spec({
            "id": "s1", "project_name": "p", "project_title": "P",
            "project_description": "d", "version": "0.1.0",
            "status": "draft", "created_at": now, "updated_at": now,
        })
        d = {
            "id": "d1", "spec_id": "s1", "sub_spec_content": "content",
            "target_agent": "agent", "status": "pending", "created_at": now,
        }
        store.create_delegation(d)
        delegations = store.get_delegations_for_spec("s1")
        assert len(delegations) == 1

        updated = store.update_delegation("d1", {"status": "completed"})
        assert updated is not None
        assert updated["status"] == "completed"

    def test_audit_crud(self, store: SQLiteStore) -> None:
        now = datetime.now(timezone.utc).isoformat()
        store.create_spec({
            "id": "s1", "project_name": "p", "project_title": "P",
            "project_description": "d", "version": "0.1.0",
            "status": "draft", "created_at": now, "updated_at": now,
        })
        a = {
            "id": "a1", "spec_id": "s1", "action": "create",
            "actor": "test", "created_at": now,
        }
        store.create_audit_record(a)
        records = store.get_audit_for_spec("s1")
        assert len(records) == 1


class TestGraphStore:
    @pytest.fixture
    def graph(self) -> GraphStore:
        return GraphStore()

    def test_add_node(self, graph: GraphStore) -> None:
        graph.add_node("n1", "module", title="Module 1")
        node = graph.get_node("n1")
        assert node is not None
        assert node["title"] == "Module 1"

    def test_add_invalid_node_type(self, graph: GraphStore) -> None:
        with pytest.raises(ValueError):
            graph.add_node("n1", "invalid_type")

    def test_add_edge(self, graph: GraphStore) -> None:
        graph.add_node("n1", "module")
        graph.add_node("n2", "module")
        graph.add_edge("n1", "n2", "depends_on")
        assert graph.has_edge("n1", "n2")

    def test_add_invalid_edge_type(self, graph: GraphStore) -> None:
        graph.add_node("n1", "module")
        graph.add_node("n2", "module")
        with pytest.raises(ValueError):
            graph.add_edge("n1", "n2", "invalid_type")

    def test_has_node(self, graph: GraphStore) -> None:
        graph.add_node("n1", "module")
        assert graph.has_node("n1")
        assert not graph.has_node("n2")

    def test_get_adjacency(self, graph: GraphStore) -> None:
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_edge("a", "b", "depends_on")
        adj = graph.get_adjacency()
        assert "a" in adj
        assert "b" in adj

    def test_get_nodes_by_type(self, graph: GraphStore) -> None:
        graph.add_node("m1", "module")
        graph.add_node("m2", "module")
        graph.add_node("e1", "api_endpoint")
        modules = graph.get_nodes_by_type("module")
        assert len(modules) == 2
        endpoints = graph.get_nodes_by_type("api_endpoint")
        assert len(endpoints) == 1

    def test_topological_sort(self, graph: GraphStore) -> None:
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_edge("a", "b", "depends_on")
        order = graph.topological_sort()
        assert order.index("a") < order.index("b")

    def test_has_cycle_false(self, graph: GraphStore) -> None:
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_edge("a", "b", "depends_on")
        assert not graph.has_cycle()

    def test_has_cycle_true(self, graph: GraphStore) -> None:
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_edge("a", "b", "depends_on")
        graph.add_edge("b", "a", "depends_on")
        assert graph.has_cycle()

    def test_to_json(self, graph: GraphStore) -> None:
        graph.add_node("n1", "module", title="M1")
        graph.add_node("n2", "module", title="M2")
        graph.add_edge("n1", "n2", "depends_on")
        j = graph.to_json()
        assert len(j["nodes"]) == 2
        assert len(j["edges"]) == 1

    def test_clear(self, graph: GraphStore) -> None:
        graph.add_node("n1", "module")
        graph.clear()
        assert not graph.has_node("n1")


class TestVectorStore:
    @pytest.fixture
    def store(self, tmp_path) -> VectorStore:
        return VectorStore(str(tmp_path / "chroma"))

    def test_add_and_search(self, store: VectorStore) -> None:
        store.add_document("doc1", "hello world", {"source": "test"})
        results = store.search("hello", n_results=5)
        assert len(results) > 0
        assert results[0]["document"] == "hello world"

    def test_delete(self, store: VectorStore) -> None:
        store.add_document("doc1", "hello world", {"source": "test"})
        store.delete_document("doc1")
        assert store.count() == 0

    def test_count(self, store: VectorStore) -> None:
        assert store.count() == 0
        store.add_document("doc1", "hello", {"source": "test"})
        assert store.count() == 1
