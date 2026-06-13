from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from specweave.persistence import SQLiteStore


class A2AHandler:
    def __init__(self, db: SQLiteStore) -> None:
        self.db = db

    def discover_specs(self) -> list[dict[str, str]]:
        specs = self.db.list_specs()
        return [{"id": s["id"], "title": s["project_title"], "status": s["status"], "version": s["version"]} for s in specs]

    def delegate(self, spec_id: str, sub_spec_content: str, target_agent: str) -> dict[str, Any]:
        delegation = {
            "id": str(uuid4()),
            "spec_id": spec_id,
            "sub_spec_content": sub_spec_content,
            "target_agent": target_agent,
            "status": "pending",
            "result": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.db.create_delegation(delegation)
        self.db.create_audit_record({
            "id": str(uuid4()),
            "spec_id": spec_id,
            "action": "delegate",
            "actor": target_agent,
            "details": {"delegation_id": delegation["id"]},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return delegation

    def submit(self, delegation_id: str, result: str) -> dict[str, Any] | None:
        delegation = self.db.get_delegation(delegation_id)
        if delegation is None:
            return None
        updated = self.db.update_delegation(delegation_id, {"status": "completed", "result": result})
        if updated:
            self.db.create_audit_record({
                "id": str(uuid4()),
                "spec_id": updated["spec_id"],
                "action": "submission",
                "actor": updated["target_agent"],
                "details": {"delegation_id": delegation_id, "result_preview": result[:200]},
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        return updated

    def impact_analysis(self, spec_id: str) -> dict[str, Any]:
        affected = []
        specs = self.db.list_specs()
        for s in specs:
            if s["id"] == spec_id:
                continue
            affected.append({"spec_id": s["id"], "title": s["project_title"]})
        return {
            "target_spec": spec_id,
            "potentially_affected": affected,
            "impact_count": len(affected),
        }
