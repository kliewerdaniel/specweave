from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS specs (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    project_title TEXT NOT NULL,
                    project_description TEXT NOT NULL,
                    version TEXT DEFAULT '0.1.0',
                    status TEXT DEFAULT 'draft',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    raw_spec TEXT DEFAULT '',
                    graph_snapshot TEXT,
                    verification_report TEXT
                );

                CREATE TABLE IF NOT EXISTS verification_gates (
                    id TEXT PRIMARY KEY,
                    spec_id TEXT NOT NULL REFERENCES specs(id),
                    gate_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    failure_reason TEXT,
                    failure_location TEXT,
                    checked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS speculations (
                    id TEXT PRIMARY KEY,
                    spec_id TEXT NOT NULL REFERENCES specs(id),
                    section_id TEXT NOT NULL,
                    candidate_index INTEGER NOT NULL,
                    architecture_description TEXT NOT NULL,
                    constraint_scores TEXT,
                    status TEXT DEFAULT 'drafted',
                    rejection_reason TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS delegations (
                    id TEXT PRIMARY KEY,
                    spec_id TEXT NOT NULL REFERENCES specs(id),
                    sub_spec_content TEXT NOT NULL,
                    target_agent TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_records (
                    id TEXT PRIMARY KEY,
                    spec_id TEXT NOT NULL REFERENCES specs(id),
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_gates_spec ON verification_gates(spec_id);
                CREATE INDEX IF NOT EXISTS idx_speculations_spec ON speculations(spec_id);
                CREATE INDEX IF NOT EXISTS idx_delegations_spec ON delegations(spec_id);
                CREATE INDEX IF NOT EXISTS idx_audit_spec ON audit_records(spec_id);
            """)

    # Spec CRUD

    def create_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO specs (id, project_name, project_title, project_description,
                   version, status, created_at, updated_at, raw_spec)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (spec["id"], spec["project_name"], spec["project_title"],
                 spec["project_description"], spec.get("version", "0.1.0"),
                 spec.get("status", "draft"), now, now, spec.get("raw_spec", "")),
            )
        return self.get_spec(spec["id"])

    def get_spec(self, spec_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM specs WHERE id = ?", (spec_id,)).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)

    def list_specs(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM specs ORDER BY created_at DESC").fetchall()
            return [self._row_to_dict(r) for r in rows]

    def update_spec(self, spec_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now
        sets = ", ".join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [spec_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE specs SET {sets} WHERE id = ?", vals)
        return self.get_spec(spec_id)

    def delete_spec(self, spec_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM specs WHERE id = ?", (spec_id,))
            return cur.rowcount > 0

    # Verification Gates

    def create_gate(self, gate: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            failure_location = gate.get("failure_location")
            if isinstance(failure_location, (dict, list)):
                failure_location = json.dumps(failure_location)
            conn.execute(
                """INSERT INTO verification_gates (id, spec_id, gate_id, status, failure_reason, failure_location, checked_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (gate["id"], gate["spec_id"], gate["gate_id"], gate.get("status", "pending"),
                 gate.get("failure_reason"), failure_location, gate.get("checked_at")),
            )
        return self.get_gate(gate["id"])

    def get_gate(self, gate_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM verification_gates WHERE id = ?", (gate_id,)).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)

    def get_gates_for_spec(self, spec_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM verification_gates WHERE spec_id = ? ORDER BY checked_at", (spec_id,)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    # Speculations

    def create_speculation(self, s: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO speculations (id, spec_id, section_id, candidate_index,
                   architecture_description, constraint_scores, status, rejection_reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (s["id"], s["spec_id"], s["section_id"], s["candidate_index"],
                 s["architecture_description"], json.dumps(s.get("constraint_scores")),
                 s.get("status", "drafted"), s.get("rejection_reason"), s["created_at"]),
            )
        return self.get_speculation(s["id"])

    def get_speculation(self, spec_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM speculations WHERE id = ?", (spec_id,)).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)

    def get_speculations_for_spec(self, spec_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM speculations WHERE spec_id = ? ORDER BY created_at", (spec_id,)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    # Delegations

    def create_delegation(self, d: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO delegations (id, spec_id, sub_spec_content, target_agent, status, result, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (d["id"], d["spec_id"], d["sub_spec_content"], d["target_agent"],
                 d.get("status", "pending"), d.get("result"), d["created_at"]),
            )
        return self.get_delegation(d["id"])

    def get_delegation(self, del_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM delegations WHERE id = ?", (del_id,)).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)

    def get_delegations_for_spec(self, spec_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM delegations WHERE spec_id = ? ORDER BY created_at", (spec_id,)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def update_delegation(self, del_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        sets = ", ".join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [del_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE delegations SET {sets} WHERE id = ?", vals)
        return self.get_delegation(del_id)

    # Audit Records

    def create_audit_record(self, a: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO audit_records (id, spec_id, action, actor, details, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (a["id"], a["spec_id"], a["action"], a["actor"],
                 json.dumps(a.get("details")), a["created_at"]),
            )
        return self.get_audit_record(a["id"])

    def get_audit_record(self, rec_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM audit_records WHERE id = ?", (rec_id,)).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)

    def get_audit_for_spec(self, spec_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_records WHERE spec_id = ? ORDER BY created_at", (spec_id,)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    # Helpers

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        for key in ("graph_snapshot", "verification_report", "failure_location", "constraint_scores", "details"):
            if key in d and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
