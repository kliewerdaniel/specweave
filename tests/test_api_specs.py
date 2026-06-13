from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestListSpecs:
    async def test_list_specs_empty(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/v2/specs", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["specs"] == []

    async def test_list_specs_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/specs")
        assert resp.status_code == 401


class TestCreateSpec:
    async def test_create_spec(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        payload = {
            "project_name": "test-proj",
            "project_title": "Test Project",
            "project_description": "A test spec",
            "version": "0.1.0",
            "raw_spec": "some spec content",
        }
        resp = await client.post("/api/v2/specs", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["spec"]["project_name"] == "test-proj"
        assert data["spec"]["status"] == "draft"

    async def test_create_spec_requires_auth(self, client: AsyncClient) -> None:
        payload = {
            "project_name": "test-proj",
            "project_title": "Test Project",
            "project_description": "A test spec",
            "raw_spec": "content",
        }
        resp = await client.post("/api/v2/specs", json=payload)
        assert resp.status_code == 401


class TestGetSpec:
    async def test_get_spec_not_found(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/v2/specs/nonexistent", headers=auth_headers)
        assert resp.status_code == 404

    async def test_get_spec_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/specs/some-id")
        assert resp.status_code == 401


class TestCompileSpec:
    async def test_compile_nonexistent(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.post("/api/v2/specs/nonexistent/compile", headers=auth_headers)
        assert resp.status_code == 404

    async def test_compile_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v2/specs/some-id/compile")
        assert resp.status_code == 401


class TestSpeculateSpec:
    async def test_speculate_nonexistent(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.post(
            "/api/v2/specs/nonexistent/speculate",
            json={"section_id": "sec-1"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_speculate_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v2/specs/some-id/speculate",
            json={"section_id": "sec-1"},
        )
        assert resp.status_code == 401


class TestVerifySpec:
    async def test_verify_nonexistent(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.post("/api/v2/specs/nonexistent/verify", headers=auth_headers)
        assert resp.status_code == 404

    async def test_verify_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v2/specs/some-id/verify")
        assert resp.status_code == 401


class TestGates:
    async def test_gates_nonexistent(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/v2/specs/nonexistent/gates", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["gates"] == []

    async def test_gates_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/specs/some-id/gates")
        assert resp.status_code == 401


class TestDelegates:
    async def test_list_delegates_nonexistent(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/v2/specs/nonexistent/delegates", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["delegations"] == []

    async def test_list_delegates_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/specs/some-id/delegates")
        assert resp.status_code == 401


class TestGraph:
    async def test_graph_nonexistent(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/v2/specs/nonexistent/graph", headers=auth_headers)
        assert resp.status_code == 404

    async def test_graph_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/specs/some-id/graph")
        assert resp.status_code == 401


class TestAudit:
    async def test_audit_empty(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/v2/specs/some-id/audit", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["records"] == []

    async def test_audit_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/specs/some-id/audit")
        assert resp.status_code == 401


class TestHealth:
    async def test_health_no_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
