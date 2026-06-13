from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from specweave.persistence import SQLiteStore


class MigrationRunner:
    def __init__(self, db: SQLiteStore) -> None:
        self.db = db

    def get_applied(self) -> list[str]:
        conn = self.db._acquire()
        try:
            rows = conn.execute("SELECT name FROM migrations ORDER BY id").fetchall()
            return [r["name"] for r in rows]
        finally:
            self.db._release(conn)

    def apply(self, name: str, migration_fn: Any) -> None:
        applied = self.get_applied()
        if name in applied:
            return
        conn = self.db._acquire()
        try:
            migration_fn(conn)
            conn.execute(
                "INSERT INTO migrations (name, applied_at) VALUES (?, ?)",
                (name, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def apply_all(self, migrations: list[tuple[str, Any]]) -> list[str]:
        applied_names: list[str] = []
        for name, migration_fn in migrations:
            self.apply(name, migration_fn)
            applied_names.append(name)
        return applied_names
