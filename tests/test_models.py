from specweave.models.spec import Spec, VerificationGate, Speculation, Delegation, AuditRecord


def test_spec_creation():
    spec = Spec(
        id="test-1",
        project_name="test",
        project_title="Test Spec",
        project_description="A test spec",
    )
    assert spec.id == "test-1"
    assert spec.status == "draft"
    assert spec.version == "0.1.0"


def test_verification_gate():
    gate = VerificationGate(spec_id="test-1", gate_id="gate1")
    assert gate.status == "pending"
    assert gate.failure_reason is None


def test_speculation():
    s = Speculation(
        spec_id="test-1",
        section_id="arch",
        candidate_index=0,
        architecture_description="Test architecture",
    )
    assert s.status == "drafted"
    assert s.rejection_reason is None


def test_delegation():
    d = Delegation(
        spec_id="test-1",
        sub_spec_content="sub content",
        target_agent="agent-x",
    )
    assert d.status == "pending"


def test_audit_record():
    a = AuditRecord(
        spec_id="test-1",
        action="create",
        actor="user-1",
        details={"key": "value"},
    )
    assert a.action == "create"
