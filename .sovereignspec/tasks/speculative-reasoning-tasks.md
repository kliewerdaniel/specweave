# Speculative Reasoning Engine — Tasks

## [P] Task 1: Speculative Engine Implementation
Status: [x] completed
Files created/modified:
  - src/specweave/speculative/engine.py
  - src/specweave/speculative/__init__.py
Dependencies: persistence-layer, neuro-symbolic-kg
Acceptance: Three-phase pipeline (draft-verify-commit) produces 2-3 candidates, scores against constraints, selects best, stores rejects with reasoning
Completed: 2026-06-13 — Full speculative engine with Ollama-based draft/verify/commit pipeline, constraint scoring, best-candidate selection, rejection tracking
