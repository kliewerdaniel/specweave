from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._pool: list[sqlite3.Connection] = []
        self._lock = threading.Lock()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _acquire(self) -> sqlite3.Connection:
        with self._lock:
            if self._pool:
                return self._pool.pop()
        return self._connect()

    def _release(self, conn: sqlite3.Connection) -> None:
        with self._lock:
            if len(self._pool) < 5:
                self._pool.append(conn)
                return
        conn.close()

    def initialize(self) -> None:
        conn = self._acquire()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS personas (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    traits TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    persona_id TEXT NOT NULL REFERENCES personas(id),
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    context TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_personas_agent ON personas(agent_id);
                CREATE INDEX IF NOT EXISTS idx_memory_persona ON memory_entries(persona_id);
                CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_entries(key);
            """)
        finally:
            self._release(conn)

    def create_persona(self, persona: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        conn = self._acquire()
        try:
            conn.execute(
                """INSERT INTO personas (id, agent_id, name, description, traits, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (persona["id"], persona["agent_id"], persona["name"],
                 persona.get("description", ""), json.dumps(persona.get("traits", {})),
                 now, now),
            )
        finally:
            self._release(conn)
        return self.get_persona(persona["id"])

    def get_persona(self, persona_id: str) -> dict[str, Any] | None:
        conn = self._acquire()
        try:
            row = conn.execute("SELECT * FROM personas WHERE id = ?", (persona_id,)).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)
        finally:
            self._release(conn)

    def list_personas(self, agent_id: str | None = None) -> list[dict[str, Any]]:
        conn = self._acquire()
        try:
            if agent_id:
                rows = conn.execute(
                    "SELECT * FROM personas WHERE agent_id = ? ORDER BY created_at DESC", (agent_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM personas ORDER BY created_at DESC").fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            self._release(conn)

    def update_persona(self, persona_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now
        if "traits" in updates and isinstance(updates["traits"], dict):
            updates["traits"] = json.dumps(updates["traits"])
        sets = ", ".join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [persona_id]
        conn = self._acquire()
        try:
            conn.execute(f"UPDATE personas SET {sets} WHERE id = ?", vals)
        finally:
            self._release(conn)
        return self.get_persona(persona_id)

    def delete_persona(self, persona_id: str) -> bool:
        conn = self._acquire()
        try:
            conn.execute("DELETE FROM memory_entries WHERE persona_id = ?", (persona_id,))
            cur = conn.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
            return cur.rowcount > 0
        finally:
            self._release(conn)

    def store_memory(self, memory: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        conn = self._acquire()
        try:
            conn.execute(
                """INSERT INTO memory_entries (id, persona_id, key, value, context, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (memory["id"], memory["persona_id"], memory["key"],
                 json.dumps(memory["value"]) if not isinstance(memory["value"], str) else memory["value"],
                 memory.get("context", ""), now),
            )
        finally:
            self._release(conn)
        return self.get_memory(memory["id"])

    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        conn = self._acquire()
        try:
            row = conn.execute("SELECT * FROM memory_entries WHERE id = ?", (memory_id,)).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)
        finally:
            self._release(conn)

    def get_memories_for_persona(self, persona_id: str) -> list[dict[str, Any]]:
        conn = self._acquire()
        try:
            rows = conn.execute(
                "SELECT * FROM memory_entries WHERE persona_id = ? ORDER BY created_at DESC", (persona_id,)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            self._release(conn)

    def search_memory(self, key: str) -> list[dict[str, Any]]:
        conn = self._acquire()
        try:
            rows = conn.execute(
                "SELECT * FROM memory_entries WHERE key LIKE ?", (f"%{key}%",)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            self._release(conn)

    def delete_memory(self, memory_id: str) -> bool:
        conn = self._acquire()
        try:
            cur = conn.execute("DELETE FROM memory_entries WHERE id = ?", (memory_id,))
            return cur.rowcount > 0
        finally:
            self._release(conn)

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        for key in ("traits", "value"):
            if key in d and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
