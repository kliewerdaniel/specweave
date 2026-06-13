# SpecWeave

> Self-verifying, speculative, multi-agent spec engine with neuro-symbolic reasoning and A2A/MCP interoperability.

SpecWeave is a **spec-driven development engine** where specifications are living, self-verifying artifacts. The spec doesn't just describe the system — it verifies itself, speculates about better architectures, delegates to other agents, and evolves. All locally. All offline.

## Architecture

SpecWeave is organized into 7 layers:

```
┌─────────────────────────────────────────────┐
│  7. Interface (Next.js Dashboard)           │
├─────────────────────────────────────────────┤
│  6. A2A/MCP Agent Gateway                   │
├─────────────────────────────────────────────┤
│  5. Self-Verifying Compiler (12 steps, 6 gates)│
├─────────────────────────────────────────────┤
│  4. Neuro-Symbolic Knowledge Graph          │
├─────────────────────────────────────────────┤
│  3. Speculative Reasoning Engine            │
├─────────────────────────────────────────────┤
│  2. Persistence (SQLite, ChromaDB, NetworkX)│
├─────────────────────────────────────────────┤
│  1. Local Inference (Ollama)                │
└─────────────────────────────────────────────┘
```

### Layer 1: Local Inference
All model execution via **Ollama** on localhost. Zero cloud dependency.

| Model | Role |
|-------|------|
| `qwen2.5-3b` | Lightweight speculator for drafting alternatives |
| `nemotron-cascade-2-30b` | Verifier for checking candidates against constraints |
| `llama3.2-8b` | General-purpose reasoning for compilation and validation |
| `nomic-embed-text` | Embedding model for vector store |

### Layer 2: Persistence
| Store | Technology | Purpose |
|-------|-----------|---------|
| Metadata DB | SQLite | Spec versions, audit records, gate statuses |
| Vector Store | ChromaDB | Semantic search over specs, ADRs, patterns |
| Knowledge Graph | NetworkX | Spec graph with 11 node types, 9 edge types |

### Layer 3: Speculative Reasoning
Three-phase pipeline: **draft** alternatives → **verify** against constraints → **commit** best candidate. GBNF grammar enforcement ensures LLM output conforms to expected JSON schemas.

### Layer 4: Neuro-Symbolic KG
Hybrid loop where **neural generates** (LLM) and **symbolic validates** (NetworkX). On failure, neural revises.

### Layer 5: Self-Verifying Compiler
12-step pipeline across 6 sequential verification gates:

| Gate | Steps | Name | Description |
|------|-------|------|-------------|
| 1 | 1-3 | Completeness | Parse, validate schema, extract constraints |
| 2 | 4-5 | Consistency | Build dependency graph, detect contradictions |
| 3 | 6-7 | Dependencies | Check drift, verify coherence |
| 4 | 8-9 | Constraints | Resolve dependencies, generate tasks |
| 5 | 10 | Coherence | Assign agents |
| 6 | 11-12 | Readiness | Set priorities, commit to audit |

### Layer 6: A2A/MCP Gateway
Dual-protocol agent federation:
- **A2A** — Agent-to-Agent: discover specs, delegate sub-specs, submit results
- **MCP** — Model Context Protocol: list and execute tools

### Layer 7: Interface
Next.js dashboard with spec visualization, speculative explorer, verification gate monitor, and agent federation status.

## Trust Model

SpecWeave uses **filesystem-based trust** — no JWT, no passwords, no cloud auth. Agents are identified by their presence in `.sovereignspec/agents/`. All agent interactions include an `X-Agent-Id` header that maps to a local agent directory.

```bash
# Agents are identified by their .sovereignspec/agents/ directory
.sovereignspec/agents/
├── opencode/
│   └── identity.json
└── claude/
    └── identity.json
```

## Quick Start

### Prerequisites
- Python 3.12+
- [Ollama](https://ollama.com) running locally
- Required models: `ollama pull qwen2.5-3b nomic-embed-text llama3.2-8b`

### Install & Run
```bash
git clone <repo-url>
cd specweave
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Initialize a project
specweave init

# Start the server
uvicorn specweave.main:app --reload --port 8000
```

### Run Tests
```bash
pytest tests/ -v
```

### CLI Usage
```bash
specweave init                          # Initialize project
specweave spec create --name my-proj --title "My Project"
specweave spec list                     # List all specs
specweave compile <spec-id>             # Run 6-gate compiler
specweave detect <spec-id>              # Contradiction/drift detection
specweave verify <spec-id>              # Neuro-symbolic verification
specweave trust                         # View trust configuration
specweave grammar                       # List GBNF grammars
specweave graph                         # View knowledge graph
specweave memory create-persona --agent-id my-agent --name "Architect"
specweave audit                         # View audit trail
specweave status                        # System status
```

## API Reference

All endpoints under `/api/v2`. Auth via `X-Agent-Id` header (filesystem-based trust).

### Specs
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v2/specs` | List all specs |
| `POST` | `/api/v2/specs` | Create spec from `.sspec` |
| `GET` | `/api/v2/specs/{id}` | Get spec with graph + verification |
| `POST` | `/api/v2/specs/{id}/compile` | Run 12-step/6-gate compiler pipeline |
| `POST` | `/api/v2/specs/{id}/speculate` | Draft alternative architectures |
| `POST` | `/api/v2/specs/{id}/verify` | Run neuro-symbolic verification |
| `GET` | `/api/v2/specs/{id}/gates` | Gate-by-gate verification status |
| `GET` | `/api/v2/specs/{id}/delegates` | List sub-spec delegations |
| `POST` | `/api/v2/specs/{id}/delegates` | Delegate sub-spec to agent |
| `GET` | `/api/v2/specs/{id}/graph` | Spec graph as adjacency list |
| `GET` | `/api/v2/specs/{id}/audit` | Full audit trail |

### A2A Protocol
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v2/a2a/specs` | Discover available specs |
| `POST` | `/api/v2/a2a/delegate` | Request sub-spec delegation |
| `POST` | `/api/v2/a2a/submit` | Submit completed sub-spec |

### MCP Protocol
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v2/mcp/tools` | List available MCP tools |
| `POST` | `/api/v2/mcp/execute` | Execute an MCP tool |

### Health
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v2/health` | Health check |

## Data Models

| Model | Description |
|-------|-------------|
| `Spec` | Spec metadata with raw content, graph snapshot, verification report |
| `VerificationGate` | Individual gate result with failure location |
| `Speculation` | Architecture candidate with constraint scores |
| `Delegation` | Sub-spec delegation to another agent |
| `AuditRecord` | Immutable audit log entry |
| `Contradiction` | Detected contradiction between spec sections |
| `Drift` | Detected drift from baseline spec |
| `Persona` | Sovereign memory persona |
| `MemoryEntry` | Key-value memory entry for a persona |

## Project Structure
```
specweave/
├── .sovereignspec/         # SovereignSpec configuration
│   ├── adr/                # Architecture Decision Records
│   ├── agents/             # Agent integration
│   ├── specs/              # .sspec specification files
│   ├── tasks/              # Task manifests
│   ├── graph/              # Knowledge graph
│   ├── memory/             # Data stores
│   ├── constitution.md     # Project constitution
│   └── sovereignspec.yaml  # LLM configuration
├── src/specweave/
│   ├── api/                # FastAPI route handlers
│   ├── compiler/           # 12-step/6-gate compiler pipeline
│   │   ├── steps.py        # 12 compilation steps
│   │   ├── gates.py        # 6 verification gates
│   │   └── pipeline.py     # Pipeline orchestrator
│   ├── detection/          # Contradiction & drift detection
│   ├── gateway/            # A2A/MCP handlers
│   ├── grammar/            # GBNF grammar files + loader
│   ├── memory/             # Sovereign memory (persona + KV store)
│   ├── models/             # Pydantic v2 data models
│   ├── neuro_symbolic/     # Neural + symbolic verification
│   ├── persistence/        # SQLite, ChromaDB, NetworkX stores
│   ├── speculative/        # Speculative reasoning engine
│   ├── cli.py              # Click CLI (specweave command)
│   ├── trust.py            # Filesystem-based trust resolution
│   ├── config.py           # Pydantic settings
│   └── main.py             # FastAPI application
├── tests/                  # pytest test suite (101 tests)
├── pyproject.toml
└── specweave.sspec         # Top-level spec document
```

## GBNF Grammar Enforcement

All LLM output is constrained by GBNF grammars to ensure valid JSON:

| Grammar | Purpose |
|---------|---------|
| `sspec.gbnf` | Spec document structure |
| `speculator.gbnf` | Speculator output (architecture candidates) |
| `verifier.gbnf` | Verifier output (constraint scores) |
| `compiler.gbnf` | Compiler pipeline output |
| `audit.gbnf` | Audit record format |

## Sovereign Memory

SpecWeave includes a built-in sovereign memory system for agent persona management:

```bash
# Create a persona
specweave memory create-persona --agent-id my-agent --name "Architect"

# Store a memory
specweave memory store --persona-id <id> --key "preference" --value "prefers functional style"

# List memories
specweave memory list-memories --persona-id <id>
```

## SovereignSpec Integration

SpecWeave is built on the **SovereignSpec** spec-driven development methodology. All features start as `.sspec` files in `.sovereignspec/specs/`.

```bash
# Validate a spec
sovereignspec spec validate <spec-id>

# Compile a spec (generate plan, tasks, and graph)
sovereignspec spec compile <spec-id>

# Generate tasks
sovereignspec tasks <spec-id>

# Cross-spec consistency analysis
sovereignspec analyze <spec-id>
```

> **Philosophy:** The specification is the durable artifact. The code is disposable. If code disagrees with spec, regenerate from spec.

## Configuration

Configuration via environment variables (prefix `SPECWEAVE_`) or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `SPECWEAVE_HOST` | `0.0.0.0` | Server bind address |
| `SPECWEAVE_PORT` | `8000` | Server port |
| `SPECWEAVE_OLLAMA_HOST` | `http://localhost:11434` | Ollama endpoint |
| `SPECWEAVE_DATA_DIR` | `.sovereignspec` | Data directory |

## License

MIT
