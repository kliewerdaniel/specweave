from __future__ import annotations

from typing import Any

from specweave.detection.models import Contradiction
from specweave.neuro_symbolic import NeuralChecker, SymbolicValidator
from specweave.persistence import GraphStore, SQLiteStore


class ContradictionDetector:
    def __init__(self, db: SQLiteStore, graph: GraphStore) -> None:
        self.db = db
        self.graph = graph
        self.symbolic = SymbolicValidator(graph)
        self.neural = NeuralChecker()

    def detect_contradictions(self, spec_id: str) -> list[Contradiction]:
        spec_data = self.db.get_spec(spec_id)
        if spec_data is None:
            return []

        contradictions: list[Contradiction] = []

        symbolic_results = self.symbolic.check_all()
        for result in symbolic_results:
            if not result["passed"]:
                contradictions.append(Contradiction(
                    spec_id=spec_id,
                    section_a="graph",
                    section_b="constraints",
                    description=result.get("failure_reason", "Symbolic check failed"),
                    severity="high",
                ))

        raw_spec = spec_data.get("raw_spec", "")
        sections = [s.strip() for s in raw_spec.split("\n\n") if s.strip()]
        for i in range(len(sections)):
            for j in range(i + 1, len(sections)):
                neural_result = self.neural.semantic_contradiction_detection(sections[i], sections[j])
                result_data = neural_result.get("result", {})
                if isinstance(result_data, dict) and result_data.get("has_contradiction"):
                    contradictions.append(Contradiction(
                        spec_id=spec_id,
                        section_a=f"section_{i}",
                        section_b=f"section_{j}",
                        description=str(result_data.get("contradictions", ["Semantic contradiction detected"])),
                        severity="medium",
                    ))

        return contradictions
