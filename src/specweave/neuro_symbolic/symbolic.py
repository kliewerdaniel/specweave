from __future__ import annotations

from typing import Any

from specweave.persistence.graph_store import GraphStore


class SymbolicValidator:
    def __init__(self, graph: GraphStore) -> None:
        self.graph = graph

    def no_circular_dependencies(self) -> dict[str, Any]:
        has_cycle = self.graph.has_cycle()
        cycle_path = self.graph.find_cycle_path() if has_cycle else []
        return {
            "name": "no_circular_dependencies",
            "passed": not has_cycle,
            "details": {"cycle_path": cycle_path} if has_cycle else {},
            "failure_reason": f"Circular dependency detected: {' -> '.join(cycle_path)}" if has_cycle else None,
        }

    def every_endpoint_has_auth(self) -> dict[str, Any]:
        endpoints = self.graph.get_nodes_by_type("api_endpoint")
        missing_auth = []
        for ep in endpoints:
            has_auth = any(
                self.graph.get_edge_data(ep, neighbor, {}).get("type") == "verifies"
                for neighbor in self.graph.graph.successors(ep)
            )
            if not has_auth:
                missing_auth.append(ep)
        return {
            "name": "every_endpoint_has_auth",
            "passed": len(missing_auth) == 0,
            "details": {"missing_auth": missing_auth},
            "failure_reason": f"Endpoints missing auth: {missing_auth}" if missing_auth else None,
        }

    def no_unresolved_dependencies(self) -> dict[str, Any]:
        modules = self.graph.get_nodes_by_type("module")
        unresolved = []
        for mod in modules:
            for dep in self.graph.graph.successors(mod):
                if not self.graph.has_node(dep):
                    unresolved.append({"module": mod, "unresolved_dep": dep})
        return {
            "name": "no_unresolved_dependencies",
            "passed": len(unresolved) == 0,
            "details": {"unresolved": unresolved},
            "failure_reason": f"Unresolved dependencies: {unresolved}" if unresolved else None,
        }

    def constraint_satisfaction(self) -> dict[str, Any]:
        constraints = self.graph.get_nodes_by_type("constraint")
        unsatisfied = []
        for c in constraints:
            has_satisfies = any(
                self.graph.get_edge_data(c, neighbor, {}).get("type") == "satisfies"
                for neighbor in self.graph.graph.successors(c)
            )
            if not has_satisfies:
                unsatisfied.append(c)
        return {
            "name": "constraint_satisfaction",
            "passed": len(unsatisfied) == 0,
            "details": {"unsatisfied": unsatisfied},
            "failure_reason": f"Unsatisfied constraints: {unsatisfied}" if unsatisfied else None,
        }

    def check_all(self) -> list[dict[str, Any]]:
        return [
            self.no_circular_dependencies(),
            self.every_endpoint_has_auth(),
            self.no_unresolved_dependencies(),
            self.constraint_satisfaction(),
        ]
