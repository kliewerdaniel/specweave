from __future__ import annotations

import logging
from typing import Any

from ollama import Client
from ollama._types import ResponseError

from specweave.config import settings

logger = logging.getLogger(__name__)


class NeuralChecker:
    def __init__(self) -> None:
        self.client = Client(host=settings.ollama_host)

    def _call_model(self, model: str, prompt: str) -> str:
        try:
            response = self.client.generate(model=model, prompt=prompt)
            return response.response.strip()
        except ResponseError as e:
            logger.warning("Ollama model '%s' not available: %s", model, e)
            return "{}"
        except Exception as e:
            logger.warning("Ollama call failed: %s", e)
            return "{}"

    def semantic_contradiction_detection(self, text_a: str, text_b: str) -> dict[str, Any]:
        prompt = (
            f"Analyze these two spec sections for contradictions.\n\n"
            f"SECTION A:\n{text_a}\n\n"
            f"SECTION B:\n{text_b}\n\n"
            "Respond with a JSON object with has_contradiction bool, "
            "contradictions list, and score 0.0-1.0"
        )
        raw = self._call_model(settings.general_model, prompt)
        return {"check": "semantic_contradiction_detection", "result": raw}

    def intent_alignment_scoring(self, intent: str, architecture: str) -> dict[str, Any]:
        prompt = (
            f"Rate how well this architecture aligns with the declared intent (0-1).\n\n"
            f"INTENT:\n{intent}\n\n"
            f"ARCHITECTURE:\n{architecture}\n\n"
            "Respond with a JSON object with alignment_score and reasoning"
        )
        raw = self._call_model(settings.general_model, prompt)
        return {"check": "intent_alignment_scoring", "result": raw}

    def architectural_coherence_check(self, architecture: str) -> dict[str, Any]:
        prompt = (
            f"Evaluate the architectural coherence of this spec (0-1).\n\n"
            f"ARCHITECTURE:\n{architecture}\n\n"
            "Respond with a JSON object with coherence_score, issues list, and recommendations list"
        )
        raw = self._call_model(settings.general_model, prompt)
        return {"check": "architectural_coherence_check", "result": raw}
