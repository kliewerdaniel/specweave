from __future__ import annotations

from typing import Any

from specweave.memory.models import Persona, MemoryEntry
from specweave.memory.store import MemoryStore


class MemoryManager:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def create_persona(self, agent_id: str, name: str, description: str = "", traits: dict[str, Any] | None = None) -> Persona:
        persona_data = {
            "id": __import__("uuid").uuid4().hex,
            "agent_id": agent_id,
            "name": name,
            "description": description,
            "traits": traits or {},
        }
        created = self.store.create_persona(persona_data)
        return Persona(**created)

    def get_persona(self, persona_id: str) -> Persona | None:
        data = self.store.get_persona(persona_id)
        if data is None:
            return None
        return Persona(**data)

    def list_personas(self, agent_id: str | None = None) -> list[Persona]:
        personas = self.store.list_personas(agent_id)
        return [Persona(**p) for p in personas]

    def update_persona(self, persona_id: str, name: str | None = None, description: str | None = None, traits: dict[str, Any] | None = None) -> Persona | None:
        updates: dict[str, Any] = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if traits is not None:
            updates["traits"] = traits
        if not updates:
            return self.get_persona(persona_id)
        updated = self.store.update_persona(persona_id, updates)
        if updated is None:
            return None
        return Persona(**updated)

    def delete_persona(self, persona_id: str) -> bool:
        return self.store.delete_persona(persona_id)

    def store_memory(self, persona_id: str, key: str, value: Any, context: str = "") -> MemoryEntry:
        memory_data = {
            "id": __import__("uuid").uuid4().hex,
            "persona_id": persona_id,
            "key": key,
            "value": value,
            "context": context,
        }
        created = self.store.store_memory(memory_data)
        return MemoryEntry(**created)

    def get_memories(self, persona_id: str) -> list[MemoryEntry]:
        memories = self.store.get_memories_for_persona(persona_id)
        return [MemoryEntry(**m) for m in memories]

    def search_memory(self, key: str) -> list[MemoryEntry]:
        memories = self.store.search_memory(key)
        return [MemoryEntry(**m) for m in memories]

    def delete_memory(self, memory_id: str) -> bool:
        return self.store.delete_memory(memory_id)
