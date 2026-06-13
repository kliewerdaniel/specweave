from __future__ import annotations

from typing import Any

from specweave.compiler.steps import CompilerSteps


class CompilerGates:
    GATE_DEFINITIONS = {
        "gate1_completeness": {
            "name": "Completeness",
            "steps": [1, 2, 3],
            "description": "Spec is complete and valid",
        },
        "gate2_consistency": {
            "name": "Consistency",
            "steps": [4, 5],
            "description": "Spec is internally consistent",
        },
        "gate3_dependencies": {
            "name": "Dependencies",
            "steps": [6, 7],
            "description": "Dependencies are resolved and coherent",
        },
        "gate4_constraints": {
            "name": "Constraints",
            "steps": [8, 9],
            "description": "Constraints are satisfied",
        },
        "gate5_coherence": {
            "name": "Coherence",
            "steps": [10],
            "description": "Architectural coherence is verified",
        },
        "gate6_readiness": {
            "name": "Readiness",
            "steps": [11, 12],
            "description": "Spec is ready for execution",
        },
    }

    def __init__(self, steps: CompilerSteps) -> None:
        self.steps = steps

    def run_gate(self, gate_id: str, spec_data: dict[str, Any]) -> dict[str, Any]:
        gate_def = self.GATE_DEFINITIONS.get(gate_id)
        if gate_def is None:
            return {"status": "failed", "failure_reason": f"Unknown gate: {gate_id}"}

        step_results = []
        for step_num in gate_def["steps"]:
            step_fn = self.steps.get_step(step_num)
            if step_fn is None:
                step_results.append({"step": step_num, "status": "failed", "error": f"Unknown step: {step_num}"})
                break
            result = step_fn(spec_data)
            step_results.append(result)
            if result["status"] == "failed":
                return {
                    "status": "failed",
                    "failure_reason": f"Step {step_num} ({result['step']}) failed: {result.get('error', 'Unknown error')}",
                    "failure_location": {"step": step_num, "gate": gate_id},
                    "step_results": step_results,
                }

        return {"status": "passed", "step_results": step_results}

    def get_gate_ids(self) -> list[str]:
        return list(self.GATE_DEFINITIONS.keys())

    def get_gate_definition(self, gate_id: str) -> dict[str, Any] | None:
        return self.GATE_DEFINITIONS.get(gate_id)
