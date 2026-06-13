from __future__ import annotations

import json

import pytest

from specweave.neuro_symbolic.neural import NeuralChecker, parse_json_response
from specweave.neuro_symbolic.symbolic import SymbolicValidator
from specweave.persistence.graph_store import GraphStore


class TestParseJsonResponse:
    def test_parses_plain_json(self) -> None:
        result = parse_json_response('{"a": 1}')
        assert result == {"a": 1}

    def test_parses_json_from_markdown_fence(self) -> None:
        result = parse_json_response("```json\n{\"a\": 1}\n```")
        assert result == {"a": 1}

    def test_parses_json_from_markdown_fence_no_lang(self) -> None:
        result = parse_json_response("```\n{\"a\": 1}\n```")
        assert result == {"a": 1}

    def test_parses_json_embedded_in_text(self) -> None:
        result = parse_json_response("Some text {\"a\": 1} more text")
        assert result == {"a": 1}

    def test_returns_none_on_garbage(self) -> None:
        result = parse_json_response("not json at all")
        assert result is None

    def test_returns_none_on_empty(self) -> None:
        result = parse_json_response("")
        assert result is None


class TestNeuralChecker:
    @pytest.fixture
    def checker(self) -> NeuralChecker:
        return NeuralChecker()

    def test_semantic_contradiction_detection_fallback(self, checker: NeuralChecker) -> None:
        result = checker.semantic_contradiction_detection("text a", "text b")
        assert result["check"] == "semantic_contradiction_detection"
        assert "result" in result

    def test_intent_alignment_scoring_fallback(self, checker: NeuralChecker) -> None:
        result = checker.intent_alignment_scoring("intent", "arch")
        assert result["check"] == "intent_alignment_scoring"
        assert "result" in result

    def test_architectural_coherence_check_fallback(self, checker: NeuralChecker) -> None:
        result = checker.architectural_coherence_check("arch")
        assert result["check"] == "architectural_coherence_check"
        assert "result" in result


class TestSymbolicValidator:
    @pytest.fixture
    def graph(self) -> GraphStore:
        return GraphStore()

    @pytest.fixture
    def validator(self, graph: GraphStore) -> SymbolicValidator:
        return SymbolicValidator(graph)

    def test_no_circular_dependencies_passes(self, validator: SymbolicValidator) -> None:
        result = validator.no_circular_dependencies()
        assert result["passed"] is True

    def test_every_endpoint_has_auth_passes(self, validator: SymbolicValidator) -> None:
        result = validator.every_endpoint_has_auth()
        assert result["passed"] is True

    def test_no_unresolved_dependencies_passes(self, validator: SymbolicValidator) -> None:
        result = validator.no_unresolved_dependencies()
        assert result["passed"] is True

    def test_constraint_satisfaction_passes(self, validator: SymbolicValidator) -> None:
        result = validator.constraint_satisfaction()
        assert result["passed"] is True

    def test_check_all(self, validator: SymbolicValidator) -> None:
        results = validator.check_all()
        assert len(results) == 4
        assert all("passed" in r for r in results)

    def test_circular_dependency_detected(self, graph: GraphStore) -> None:
        graph.add_node("a", "module")
        graph.add_node("b", "module")
        graph.add_edge("a", "b", "depends_on")
        graph.add_edge("b", "a", "depends_on")
        validator = SymbolicValidator(graph)
        result = validator.no_circular_dependencies()
        assert result["passed"] is False
