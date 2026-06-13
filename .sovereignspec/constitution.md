# Project Constitution

## Technology Stack
- Language: Python 3.12+
- Framework: FastAPI
- Database: SQLite via sqlite3 (no ORM)
- Vector Store: ChromaDB
- Knowledge Graph: NetworkX
- Validation: Pydantic v2
- Auth: JWT (python-jose + passlib)
- LLM Client: ollama-python
- Testing: pytest + httpx

## Architectural Rules
1. No ORM — raw SQL with sqlite3
2. All handlers are async
3. Functional core with imperative shell
4. Type hints on every function signature
5. All inference via Ollama — zero cloud APIs
6. No telemetry or external data collection
7. GBNF grammar enforcement for all LLM output

## Architecture: 7-Layer SpecWeave
1. **Local Inference** — Ollama/llama.cpp model execution
2. **Persistence** — SQLite + ChromaDB + NetworkX
3. **Speculative Reasoning** — Draft alternatives, verify, commit
4. **Neuro-Symbolic KG** — Neural generation + symbolic validation
5. **Self-Verifying Compiler** — 12-step, 6-gate pipeline
6. **A2A/MCP Agent Gateway** — Agent federation
7. **Interface** — Next.js dashboard

## Non-Negotiable Constraints
- Zero cloud dependencies
- All secrets via environment variables
- Tests required for every endpoint
- Every decision produces an audit record
- Offline-capable at all times
