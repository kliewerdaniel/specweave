import pytest
from fastapi.testclient import TestClient

from specweave.auth import create_access_token
from specweave.main import app

client = TestClient(app)

TEST_TOKEN = create_access_token("test-user")


def test_health_check():
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unauthenticated_request():
    response = client.get("/api/v2/specs")
    assert response.status_code == 401


def test_create_spec():
    response = client.post(
        "/api/v2/specs",
        json={
            "project_name": "test",
            "project_title": "Test Spec",
            "project_description": "A test spec",
            "version": "1.0.0",
            "raw_spec": "content: test",
        },
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["spec"]["project_title"] == "Test Spec"
    assert data["spec"]["status"] == "draft"
    spec_id = data["spec"]["id"]
    return spec_id


def test_list_specs():
    test_create_spec()
    response = client.get(
        "/api/v2/specs",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["specs"]) >= 1


def test_get_spec():
    spec_id = test_create_spec()
    response = client.get(
        f"/api/v2/specs/{spec_id}",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200
    assert response.json()["spec"]["id"] == spec_id


def test_get_nonexistent_spec():
    response = client.get(
        "/api/v2/specs/nonexistent",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 404


def test_compile_spec():
    spec_id = test_create_spec()
    response = client.post(
        f"/api/v2/specs/{spec_id}/compile",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["spec_id"] == spec_id
    assert len(data["gates"]) > 0


def test_get_gates():
    spec_id = test_create_spec()
    client.post(
        f"/api/v2/specs/{spec_id}/compile",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    response = client.get(
        f"/api/v2/specs/{spec_id}/gates",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200
    assert len(response.json()["gates"]) > 0


def test_speculate():
    spec_id = test_create_spec()
    response = client.post(
        f"/api/v2/specs/{spec_id}/speculate",
        json={"section_id": "architecture"},
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200


def test_verify_spec():
    spec_id = test_create_spec()
    response = client.post(
        f"/api/v2/specs/{spec_id}/verify",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200


def test_delegation_flow():
    spec_id = test_create_spec()
    response = client.post(
        f"/api/v2/specs/{spec_id}/delegates",
        json={
            "sub_spec_content": "sub-spec content",
            "target_agent": "agent-x",
        },
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200
    del_id = response.json()["delegation"]["id"]

    response = client.get(
        f"/api/v2/specs/{spec_id}/delegates",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200
    assert len(response.json()["delegations"]) >= 1


def test_graph():
    spec_id = test_create_spec()
    response = client.get(
        f"/api/v2/specs/{spec_id}/graph",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200


def test_audit_trail():
    spec_id = test_create_spec()
    response = client.get(
        f"/api/v2/specs/{spec_id}/audit",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200


def test_a2a_discover():
    test_create_spec()
    response = client.get(
        "/api/v2/a2a/specs",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200


def test_a2a_delegate():
    spec_id = test_create_spec()
    response = client.post(
        "/api/v2/a2a/delegate",
        json={
            "spec_id": spec_id,
            "sub_spec_content": "content",
            "target_agent": "agent-y",
        },
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200
    assert "delegation_id" in response.json()


def test_mcp_tools():
    response = client.get(
        "/api/v2/mcp/tools",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200
    assert len(response.json()["tools"]) > 0


def test_mcp_execute():
    response = client.post(
        "/api/v2/mcp/execute",
        json={"tool": "list_specs", "params": {}},
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 200


def test_mcp_execute_unknown_tool():
    response = client.post(
        "/api/v2/mcp/execute",
        json={"tool": "unknown_tool", "params": {}},
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 400
