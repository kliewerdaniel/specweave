from __future__ import annotations

from typing import Any
from uuid import uuid4

from specweave.neuro_symbolic import NeuralChecker, SymbolicValidator
from specweave.persistence import GraphStore, SQLiteStore


class CompilerSteps:
    def __init__(self, db: SQLiteStore, graph: GraphStore) -> None:
        self.db = db
        self.graph = graph
        self.symbolic = SymbolicValidator(graph)
        self.neural = NeuralChecker()

    def step1_parse_spec(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        raw = spec_data.get("raw_spec", "")
        if not raw.strip():
            return {"step": "parse_spec", "status": "failed", "error": "Empty raw_spec"}
        return {"step": "parse_spec", "status": "passed", "details": {"raw_length": len(raw)}}

    def step2_validate_schema(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        required = ["id", "project_name", "project_title", "project_description", "version", "raw_spec"]
        missing = [f for f in required if not spec_data.get(f)]
        if missing:
            return {"step": "validate_schema", "status": "failed", "error": f"Missing fields: {missing}"}
        return {"step": "validate_schema", "status": "passed"}

    def step3_extract_constraints(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        raw = spec_data.get("raw_spec", "")
        constraints = []
        keywords = ["must", "shall", "required", "mandatory", "constraint"]
        for line in raw.split("\n"):
            for kw in keywords:
                if kw in line.lower():
                    constraints.append(line.strip())
                    break
        return {"step": "extract_constraints", "status": "passed", "details": {"constraints_found": len(constraints)}}

    def step4_build_dependency_graph(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        spec_id = spec_data.get("id", "")
        if spec_id and not self.graph.has_node(spec_id):
            self.graph.add_node(
                spec_id,
                node_type="spec_section",
                title=spec_data.get("project_title", ""),
                status=spec_data.get("status", "draft"),
            )
        return {"step": "build_dependency_graph", "status": "passed"}

    def step5_detect_contradictions(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        results = self.symbolic.check_all()
        failures = [r for r in results if not r["passed"]]
        if failures:
            return {
                "step": "detect_contradictions",
                "status": "failed",
                "error": f"Contradictions found: {[f['name'] for f in failures]}",
            }
        return {"step": "detect_contradictions", "status": "passed"}

    def step6_check_drift(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        return {"step": "check_drift", "status": "passed", "details": {"note": "No baseline to compare against"}}

    def step7_verify_coherence(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        intent = spec_data.get("project_description", "")
        layers = str(spec_data.get("graph_snapshot", {}))
        neural_result = self.neural.architectural_coherence_check(
            f"Intent: {intent}\n\nArchitecture layers: {layers}"
        )
        result_data = neural_result.get("result", {})
        coherence_score = result_data.get("coherence_score", 0.0) if isinstance(result_data, dict) else 0.0
        if coherence_score < 0.5:
            issues = result_data.get("issues", ["Low coherence score"]) if isinstance(result_data, dict) else ["Low coherence score"]
            return {
                "step": "verify_coherence",
                "status": "failed",
                "error": f"Coherence score {coherence_score} below threshold",
            }
        return {"step": "verify_coherence", "status": "passed", "details": {"coherence_score": coherence_score}}

    def step8_resolve_dependencies(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        deps_result = self.symbolic.no_circular_dependencies()
        resolved_result = self.symbolic.no_unresolved_dependencies()
        if not deps_result["passed"]:
            return {"step": "resolve_dependencies", "status": "failed", "error": deps_result["failure_reason"]}
        if not resolved_result["passed"]:
            return {"step": "resolve_dependencies", "status": "failed", "error": resolved_result["failure_reason"]}
        return {"step": "resolve_dependencies", "status": "passed"}

    def step9_generate_tasks(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        return {"step": "generate_tasks", "status": "passed", "details": {"tasks_generated": 0}}

    def step10_assign_agents(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        return {"step": "assign_agents", "status": "passed", "details": {"agents_assigned": 0}}

    def step11_set_priorities(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        return {"step": "set_priorities", "status": "passed", "details": {"priorities_set": 0}}

    def step12_commit_to_audit(self, spec_data: dict[str, Any]) -> dict[str, Any]:
        return {"step": "commit_to_audit", "status": "passed"}

    def get_step(self, step_num: int) -> Any:
        steps = {
            1: self.step1_parse_spec,
            2: self.step2_validate_schema,
            3: self.step3_extract_constraints,
            4: self.step4_build_dependency_graph,
            5: self.step5_detect_contradictions,
            6: self.step6_check_drift,
            7: self.step7_verify_coherence,
            8: self.step8_resolve_dependencies,
            9: self.step9_generate_tasks,
            10: self.step10_assign_agents,
            11: self.step11_set_priorities,
            12: self.step12_commit_to_audit,
        }
        return steps.get(step_num)
