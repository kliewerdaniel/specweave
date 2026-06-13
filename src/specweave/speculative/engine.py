from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ollama import Client
from ollama._types import ResponseError

from specweave.config import settings

logger = logging.getLogger(__name__)


class SpeculativeEngine:
    SPECULATOR_PROMPT = (
        "You are a software architecture speculator. Given a spec section, "
        "draft 2-3 alternative architectures. Be creative but practical.\n\n"
        "SECTION:\n{section_content}\n\n"
        "Respond with a JSON array of objects, each with keys: "
        "architecture_description (str), rationale (str), tradeoffs (list[str])"
    )

    VERIFIER_PROMPT = (
        "You are an architecture verifier. Evaluate this candidate architecture "
        "against these constraints. Score each constraint 0.0-1.0.\n\n"
        "ARCHITECTURE:\n{architecture}\n\n"
        "CONSTRAINTS:\n{constraints}\n\n"
        "Respond with a JSON object with scores dict, overall score, "
        "verdict (accept/reject), and reasoning"
    )

    def __init__(self) -> None:
        self.client = Client(host=settings.ollama_host)

    def _generate(self, model: str, prompt: str) -> str:
        try:
            response = self.client.generate(model=model, prompt=prompt)
            return response.response.strip()
        except ResponseError as e:
            logger.warning("Ollama model '%s' not available: %s", model, e)
            return "[]"
        except Exception as e:
            logger.warning("Ollama call failed: %s", e)
            return "[]"

    def speculate(self, spec_id: str, section_id: str, section_content: str, constraints: list[str]) -> list[dict[str, Any]]:
        prompt = self.SPECULATOR_PROMPT.format(section_content=section_content)
        candidates_text = self._generate(settings.speculator_model, prompt)

        try:
            candidates = json.loads(candidates_text)
        except json.JSONDecodeError:
            candidates = [{"architecture_description": candidates_text, "rationale": "", "tradeoffs": []}]

        if not candidates:
            candidates = [{"architecture_description": "Default architecture", "rationale": "", "tradeoffs": []}]

        results = []
        for i, candidate in enumerate(candidates[:3]):
            cand_id = str(uuid4())
            created_at = datetime.now(timezone.utc).isoformat()

            ver_prompt = self.VERIFIER_PROMPT.format(
                architecture=candidate.get("architecture_description", ""),
                constraints="\n".join(f"- {c}" for c in constraints),
            )
            ver_raw = self._generate(settings.verifier_model, ver_prompt)

            scores = {}
            verdict = "accept"
            try:
                ver_result = json.loads(ver_raw)
                if isinstance(ver_result, dict):
                    scores = ver_result.get("scores", {})
                    verdict = ver_result.get("verdict", "accept")
            except (json.JSONDecodeError, TypeError):
                pass

            results.append({
                "id": cand_id,
                "spec_id": spec_id,
                "section_id": section_id,
                "candidate_index": i,
                "architecture_description": candidate.get("architecture_description", ""),
                "constraint_scores": scores,
                "status": "committed" if verdict == "accept" else "verified",
                "rejection_reason": None if verdict == "accept" else f"Verdict: {verdict}",
                "created_at": created_at,
            })

        best_idx = 0
        best_score = -1
        for i, r in enumerate(results):
            ss = r.get("constraint_scores") or {}
            score = sum(v for v in ss.values() if isinstance(v, (int, float)))
            if score > best_score:
                best_score = score
                best_idx = i

        for i, r in enumerate(results):
            if i != best_idx and r["status"] != "committed":
                r["status"] = "rejected"
                r["rejection_reason"] = r.get("rejection_reason") or "Not the best candidate"

        return results
