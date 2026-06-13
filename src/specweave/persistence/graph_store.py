from __future__ import annotations

from threading import RLock
from typing import Any

import networkx as nx


class GraphStore:
    VALID_NODE_TYPES = {
        "spec_section", "module", "api_endpoint", "data_model",
        "constraint", "dependency", "agent", "verification_gate",
        "rejected_proposal", "audit_record", "persona",
    }

    VALID_EDGE_TYPES = {
        "depends_on", "validates", "generates", "delegates_to",
        "contradicts", "satisfies", "evolves_from", "verifies", "rejects",
    }

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self._lock = RLock()

    def add_node(self, node_id: str, node_type: str, **attrs: Any) -> None:
        if node_type not in self.VALID_NODE_TYPES:
            msg = f"Invalid node type: {node_type}. Valid: {self.VALID_NODE_TYPES}"
            raise ValueError(msg)
        with self._lock:
            self.graph.add_node(node_id, type=node_type, **attrs)

    def add_edge(self, u: str, v: str, edge_type: str, **attrs: Any) -> None:
        if edge_type not in self.VALID_EDGE_TYPES:
            msg = f"Invalid edge type: {edge_type}. Valid: {self.VALID_EDGE_TYPES}"
            raise ValueError(msg)
        with self._lock:
            self.graph.add_edge(u, v, type=edge_type, **attrs)

    def has_node(self, node_id: str) -> bool:
        with self._lock:
            return self.graph.has_node(node_id)

    def has_edge(self, u: str, v: str) -> bool:
        with self._lock:
            return self.graph.has_edge(u, v)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        with self._lock:
            if not self.graph.has_node(node_id):
                return None
            data = dict(self.graph.nodes[node_id])
            data["id"] = node_id
            return data

    def get_neighbors(self, node_id: str) -> list[dict[str, Any]]:
        with self._lock:
            if not self.graph.has_node(node_id):
                return []
            result = []
            for neighbor in self.graph.successors(node_id):
                edge_data = self.graph.get_edge_data(node_id, neighbor)
                result.append({
                    "target": neighbor,
                    "edge_type": edge_data.get("type", "unknown") if edge_data else "unknown",
                })
            return result

    def get_adjacency(self) -> dict[str, list[str]]:
        with self._lock:
            adj: dict[str, list[str]] = {}
            for u, v in self.graph.edges():
                adj.setdefault(u, []).append(v)
                adj.setdefault(v, [])
            for node in self.graph.nodes():
                adj.setdefault(node, [])
            return adj

    def get_nodes_by_type(self, node_type: str) -> list[str]:
        with self._lock:
            return [
                n for n, d in self.graph.nodes(data=True)
                if d.get("type") == node_type
            ]

    def topological_sort(self) -> list[str]:
        with self._lock:
            try:
                return list(nx.topological_sort(self.graph))
            except nx.NetworkXUnfeasible:
                return []

    def has_cycle(self) -> bool:
        with self._lock:
            try:
                nx.find_cycle(self.graph)
                return True
            except nx.NetworkXNoCycle:
                return False

    def find_cycle_path(self) -> list[str]:
        with self._lock:
            try:
                cycle = nx.find_cycle(self.graph)
                return [edge[0] for edge in cycle] + [cycle[0][0]]
            except nx.NetworkXNoCycle:
                return []

    def to_json(self) -> dict[str, Any]:
        with self._lock:
            return {
                "nodes": [
                    {"id": n, **d}
                    for n, d in self.graph.nodes(data=True)
                ],
                "edges": [
                    {"source": u, "target": v, **d}
                    for u, v, d in self.graph.edges(data=True)
                ],
            }

    def clear(self) -> None:
        with self._lock:
            self.graph.clear()
