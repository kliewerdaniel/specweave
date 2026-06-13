from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from specweave.config import settings

logger = logging.getLogger(__name__)


class AgentIdentity:
    def __init__(self, agent_id: str, source_path: Path) -> None:
        self.agent_id = agent_id
        self.source_path = source_path

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AgentIdentity):
            return NotImplemented
        return self.agent_id == other.agent_id

    def __hash__(self) -> int:
        return hash(self.agent_id)

    def __repr__(self) -> str:
        return f"AgentIdentity(agent_id={self.agent_id!r})"


def discover_agents() -> list[AgentIdentity]:
    data_dir = settings.data_dir
    agents_dir = data_dir / "agents"
    if not agents_dir.exists():
        return []
    agents: list[AgentIdentity] = []
    for entry in sorted(agents_dir.iterdir()):
        if entry.is_dir():
            identity_file = entry / "identity.json"
            if identity_file.exists():
                agents.append(AgentIdentity(agent_id=entry.name, source_path=entry))
            else:
                agents.append(AgentIdentity(agent_id=entry.name, source_path=entry))
    return agents


def resolve_agent_identity(agent_id: str) -> AgentIdentity | None:
    data_dir = settings.data_dir
    agent_path = data_dir / "agents" / agent_id
    if agent_path.exists() and agent_path.is_dir():
        return AgentIdentity(agent_id=agent_id, source_path=agent_path)
    return None


def read_bootstrap() -> dict[str, Any] | None:
    data_dir = settings.data_dir
    bootstrap_path = data_dir / "bootstrap.md"
    if not bootstrap_path.exists():
        return None
    content = bootstrap_path.read_text()
    return {"path": str(bootstrap_path), "content": content}


def compute_trust_hash(agent_id: str) -> str:
    return hashlib.sha256(agent_id.encode()).hexdigest()[:16]


class TrustResolver:
    def __init__(self, request: Request) -> None:
        self.request = request

    async def resolve(self) -> AgentIdentity:
        agent_id = self.request.headers.get("X-Agent-Id", "")
        if not agent_id:
            agent_id = self.request.query_params.get("agent_id", "")

        if agent_id:
            identity = resolve_agent_identity(agent_id)
            if identity is not None:
                return identity
            return AgentIdentity(agent_id=agent_id, source_path=Path("."))

        bootstrap = read_bootstrap()
        if bootstrap is not None:
            default_agent = settings.data_dir / "agents" / "default"
            if default_agent.exists():
                return AgentIdentity(agent_id="default", source_path=default_agent)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No agent identity provided. Set X-Agent-Id header or provide agent_id query parameter.",
        )


async def get_current_agent(request: Request) -> AgentIdentity:
    resolver = TrustResolver(request)
    return await resolver.resolve()


def get_agent_id(agent: AgentIdentity) -> str:
    return agent.agent_id
