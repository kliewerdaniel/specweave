# Core Engine — Tasks

## [P] Task 1: FastAPI Application Setup
Status: [x] completed
Files created/modified:
  - src/specweave/main.py
  - src/specweave/config.py
  - pyproject.toml
Dependencies: None
Acceptance: FastAPI app initializes with CORS, routers, and lifespan lifecycle management
Completed: 2026-06-13 — FastAPI application with lifespan that initializes SQLite and NetworkX graph stores

## [P] Task 2: JWT Authentication
Status: [x] completed
Files created/modified:
  - src/specweave/auth.py
Dependencies: None
Acceptance: JWT token creation, verification, and Bearer auth dependency works for all endpoints except /health
Completed: 2026-06-13 — JWT authentication with create/verify tokens, Bearer security, password hashing via passlib

## [P] Task 3: Data Models
Status: [x] completed
Files created/modified:
  - src/specweave/models/spec.py
  - src/specweave/models/__init__.py
Dependencies: None
Acceptance: All Pydantic v2 models defined for Spec, VerificationGate, Speculation, Delegation, AuditRecord, and all request/response schemas
Completed: 2026-06-13 — Full Pydantic v2 model suite with all request/response schemas for the API

## [P] Task 4: API Routes — Spec Management
Status: [x] completed
Files created/modified:
  - src/specweave/api/specs.py
  - src/specweave/api/__init__.py
Dependencies: persistence-layer, self-verifying-compiler, speculative-reasoning, neuro-symbolic-kg, a2a-mcp-gateway
Acceptance: All spec CRUD endpoints work: list, create, get, compile, speculate, verify, gates, delegates, graph, audit
Completed: 2026-06-13 — Complete spec management API with 12 endpoints

## [P] Task 5: API Routes — Gateway
Status: [x] completed
Files created/modified:
  - src/specweave/api/gateway.py
  - src/specweave/api/health.py
Dependencies: a2a-mcp-gateway
Acceptance: A2A, MCP, and health endpoints work correctly
Completed: 2026-06-13 — Gateway API with A2A discover/delegate/submit, MCP tools/execute, and health endpoints

## [P] Task 6: Tests
Status: [x] completed
Files created/modified:
  - tests/test_api.py
  - tests/test_models.py
  - tests/test_persistence.py
Dependencies: core-engine
Acceptance: All tests pass — 40 tests covering API, models, and persistence layers
Completed: 2026-06-13 — 40 tests covering all API endpoints, models, and persistence stores
