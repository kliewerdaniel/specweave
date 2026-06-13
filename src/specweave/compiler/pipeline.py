from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from specweave.compiler.gates import CompilerGates
from specweave.compiler.steps import CompilerSteps
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
        self.steps = CompilerSteps(db, graph)
        self.gates = CompilerGates(self.steps)

    def run(self, spec_id: str, spec_data: dict[str, Any]) -> list[dict[str, Any]]:
        gate_results = []
        for gate_id in self.GATES:
            gate_result = self.gates.run_gate(gate_id, spec_data)
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
            gate_results.append(gate_record)

            if gate_result["status"] == "failed":
                break

        final_status = "compiled" if all(g["status"] == "passed" for g in gate_results) else "failed"
        self.db.update_spec(spec_id, {"status": final_status})
        self.db.create_audit_record({
            "id": str(uuid4()),
            "spec_id": spec_id,
            "action": "compile",
            "actor": "compiler",
            "details": {"gates": gate_results, "final_status": final_status},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        return gate_results
