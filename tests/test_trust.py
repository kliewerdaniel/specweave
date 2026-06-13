from __future__ import annotations

from pathlib import Path

import pytest

from specweave.config import settings
from specweave.trust import (
    AgentIdentity,
    TrustResolver,
    compute_trust_hash,
    discover_agents,
    read_bootstrap,
    resolve_agent_identity,
)


class TestAgentIdentity:
    def test_equality(self) -> None:
        a = AgentIdentity(agent_id="agent-1", source_path=Path("."))
        b = AgentIdentity(agent_id="agent-1", source_path=Path("/other"))
        assert a == b

    def test_inequality(self) -> None:
        a = AgentIdentity(agent_id="agent-1", source_path=Path("."))
        b = AgentIdentity(agent_id="agent-2", source_path=Path("."))
        assert a != b

    def test_hash(self) -> None:
        a = AgentIdentity(agent_id="agent-1", source_path=Path("."))
        b = AgentIdentity(agent_id="agent-1", source_path=Path("/other"))
        assert hash(a) == hash(b)

    def test_repr(self) -> None:
        a = AgentIdentity(agent_id="agent-1", source_path=Path("."))
        assert "agent-1" in repr(a)


class TestDiscoverAgents:
    def test_discover_empty(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        settings.data_dir = empty_dir
        agents = discover_agents()
        assert agents == []

    def test_discover_with_agents(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "custom" / ".sovereignspec"
        agent_dir = data_dir / "agents" / "my-agent"
        agent_dir.mkdir(parents=True)
        settings.data_dir = data_dir
        agents = discover_agents()
        assert len(agents) == 1
        assert agents[0].agent_id == "my-agent"


class TestResolveAgentIdentity:
    def test_resolve_existing(self, tmp_path: Path) -> None:
        settings.data_dir = tmp_path / ".sovereignspec"
        agent_dir = settings.data_dir / "agents" / "my-agent"
        agent_dir.mkdir(parents=True)
        identity = resolve_agent_identity("my-agent")
        assert identity is not None
        assert identity.agent_id == "my-agent"

    def test_resolve_nonexistent(self, tmp_path: Path) -> None:
        settings.data_dir = tmp_path / ".sovereignspec"
        identity = resolve_agent_identity("nonexistent")
        assert identity is None


class TestReadBootstrap:
    def test_read_bootstrap_exists(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "sbtest"
        data_dir.mkdir(parents=True)
        settings.data_dir = data_dir
        bootstrap = data_dir / "bootstrap.md"
        bootstrap.write_text("# Bootstrap\nAgent identity config")
        result = read_bootstrap()
        assert result is not None
        assert "Bootstrap" in result["content"]

    def test_read_bootstrap_missing(self, tmp_path: Path) -> None:
        settings.data_dir = tmp_path / "empty"
        result = read_bootstrap()
        assert result is None


class TestComputeTrustHash:
    def test_deterministic(self) -> None:
        h1 = compute_trust_hash("agent-1")
        h2 = compute_trust_hash("agent-1")
        assert h1 == h2

    def test_different_agents(self) -> None:
        h1 = compute_trust_hash("agent-1")
        h2 = compute_trust_hash("agent-2")
        assert h1 != h2

    def test_length(self) -> None:
        h = compute_trust_hash("agent-1")
        assert len(h) == 16
