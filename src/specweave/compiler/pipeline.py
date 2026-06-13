from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from specweave.neuro_symbolic import NeuralChecker, SymbolicValidator
from specweave.persistence import GraphStore, SQLiteStore


class CompilerPipeline:
    GATES = [
        "gate1_completeness",
        "gate2_consistency",
        "gate3_dependencies",
        "gate4_constraints",
        "gate5_coherence",
        "gate6_readiness",
    ]

    def __init__(self, db: SQLiteStore, graph: GraphStore) -> None:
        self.db = db
        self.graph = graph
        self.symbolic = SymbolicValidator(graph)
        self.neural = NeuralChecker()

    def run(self, spec_id: str, spec_data: dict[str, Any]) -> list[dict[str, Any]]:
        gates = []
        for gate_id in self.GATES:
            gate_result = self._run_gate(gate_id, spec_data)
            gate_record = {
                "id": str(uuid4()),
                "spec_id": spec_id,
                "gate_id": gate_id,
                "status": gate_result["status"],
                "failure_reason": gate_result.get("failure_reason"),
                "failure_location": gate_result.get("failure_location"),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            self.db.create_gate(gate_record)
            gates.append(gate_record)

            if gate_result["status"] == "failed":
                break

        final_status = "compiled" if all(g["status"] == "passed" for g in gates) else "failed"
        self.db.update_spec(spec_id, {"status": final_status})
        self.db.create_audit_record({
            "id": str(uuid4()),
            "spec_id": spec_id,
            "action": "compile",
            "actor": "compiler",
            "details": {"gates": gates, "final_status": final_status},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        return gates

    def _run_gate(self, gate_id: str, spec_data: dict[str, Any]) -> dict[str, Any]:
        handlers = {
            "gate1_completeness": self._gate_completeness,
            "gate2_consistency": self._gate_consistency,
            "gate3_dependencies": self._gate_dependencies,
            "gate4_constraints": self._gate_constraints,
            "gate5_coherence": self._gate_coherence,
            "gate6_readiness": self._gate_readiness,
        }
        handler = handlers.get(gate_id)
        if handler is None:
            return {"status": "failed", "failure_reason": f"Unknown gate: {gate_id}"}
        return handler(spec_data)

    def _gate_completeness(self, spec: dict[str, Any]) -> dict[str, Any]:
        required = ["project_name", "project_title", "project_description", "version"]
        missing = [f for f in required if not spec.get(f)]
        if missing:
            return {
                "status": "failed",
                "failure_reason": f"Missing required fields: {missing}",
                "failure_location": {"missing_fields": missing},
            }
        return {"status": "passed"}

    def _gate_consistency(self, spec: dict[str, Any]) -> dict[str, Any]:
        results = self.symbolic.check_all()
        failures = [r for r in results if not r["passed"]]
        if failures:
            return {
                "status": "failed",
                "failure_reason": f"Consistency checks failed: {[f['name'] for f in failures]}",
                "failure_location": {"failures": failures},
            }
        return {"status": "passed"}

    def _gate_dependencies(self, spec: dict[str, Any]) -> dict[str, Any]:
        deps_result = self.symbolic.no_circular_dependencies()
        resolved_result = self.symbolic.no_unresolved_dependencies()
        if not deps_result["passed"]:
            return {
                "status": "failed",
                "failure_reason": deps_result["failure_reason"],
                "failure_location": deps_result["details"],
            }
        if not resolved_result["passed"]:
            return {
                "status": "failed",
                "failure_reason": resolved_result["failure_reason"],
                "failure_location": resolved_result["details"],
            }
        return {"status": "passed"}

    def _gate_constraints(self, spec: dict[str, Any]) -> dict[str, Any]:
        constraint_result = self.symbolic.constraint_satisfaction()
        if not constraint_result["passed"]:
            return {
                "status": "failed",
                "failure_reason": constraint_result["failure_reason"],
                "failure_location": constraint_result["details"],
            }
        return {"status": "passed"}

    def _gate_coherence(self, spec: dict[str, Any]) -> dict[str, Any]:
        intent = spec.get("project_description", "")
        layers = str(spec.get("graph_snapshot", {}))
        result = self.neural.architectural_coherence_check(
            f"Intent: {intent}\n\nArchitecture layers: {layers}"
        )
        return {"status": "passed", "details": result}

    def _gate_readiness(self, spec: dict[str, Any]) -> dict[str, Any]:
        modules = self.graph.get_nodes_by_type("module")
        endpoints = self.graph.get_nodes_by_type("api_endpoint")
        if not modules and not endpoints:
            return {
                "status": "failed",
                "failure_reason": "No modules or endpoints defined in graph",
                "failure_location": {"modules": 0, "endpoints": 0},
            }
        return {"status": "passed", "details": {"modules": len(modules), "endpoints": len(endpoints)}}
