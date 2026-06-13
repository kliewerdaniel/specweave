from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from specweave.speculative.engine import SpeculativeEngine, parse_json_response


class TestParseJsonResponse:
    def test_parses_array(self) -> None:
        result = parse_json_response('[{"a": 1}]')
        assert result == [{"a": 1}]

    def test_parses_object(self) -> None:
        result = parse_json_response('{"a": 1}')
        assert result == {"a": 1}

    def test_parses_markdown_fence(self) -> None:
        result = parse_json_response("```json\n[1, 2, 3]\n```")
        assert result == [1, 2, 3]

    def test_fallback_on_garbage(self) -> None:
        result = parse_json_response("not json")
        assert result is None


class TestSpeculativeEngine:
    @pytest.fixture
    def engine(self) -> SpeculativeEngine:
        return SpeculativeEngine()

    def test_speculate_with_mock(self, engine: SpeculativeEngine) -> None:
        mock_response = MagicMock()
        mock_response.response = '[{"architecture_description": "arch1", "rationale": "r1", "tradeoffs": []}]'
        engine.client.generate = MagicMock(return_value=mock_response)

        results = engine.speculate(
            spec_id="s1",
            section_id="sec-1",
            section_content="content",
            constraints=["local-first"],
        )
        assert len(results) > 0
        assert results[0]["spec_id"] == "s1"
        assert results[0]["section_id"] == "sec-1"

    def test_speculate_handles_empty_response(self, engine: SpeculativeEngine) -> None:
        mock_response = MagicMock()
        mock_response.response = ""
        engine.client.generate = MagicMock(return_value=mock_response)

        results = engine.speculate(
            spec_id="s1",
            section_id="sec-1",
            section_content="content",
            constraints=["local-first"],
        )
        assert len(results) == 1

    def test_verify(self, engine: SpeculativeEngine) -> None:
        mock_response = MagicMock()
        mock_response.response = '{"scores": {"score": 0.9}, "overall": 0.9, "verdict": "accept", "reasoning": "good"}'
        engine.client.generate = MagicMock(return_value=mock_response)

        results = engine.speculate(
            spec_id="s1",
            section_id="sec-1",
            section_content="content",
            constraints=["local-first"],
        )
        assert len(results) > 0
