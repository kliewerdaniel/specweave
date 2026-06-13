from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from specweave.models.spec import DelegationStatus
from specweave.persistence import SQLiteStore

DELEGATION_TIMEOUT_SECONDS = 3600


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
            "ttl_seconds": DELEGATION_TIMEOUT_SECONDS,
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
        if delegation.get("status") not in ("pending", "in_progress"):
            return delegation
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

    def start(self, delegation_id: str) -> dict[str, Any] | None:
        delegation = self.db.get_delegation(delegation_id)
        if delegation is None:
            return None
        return self.db.update_delegation(delegation_id, {"status": "in_progress"})

    def fail(self, delegation_id: str, reason: str) -> dict[str, Any] | None:
        delegation = self.db.get_delegation(delegation_id)
        if delegation is None:
            return None
        return self.db.update_delegation(delegation_id, {"status": "failed", "result": reason})

    def retry(self, delegation_id: str) -> dict[str, Any] | None:
        delegation = self.db.get_delegation(delegation_id)
        if delegation is None:
            return None
        if delegation.get("status") != "failed":
            return delegation
        return self.db.update_delegation(delegation_id, {"status": "pending", "result": None})

    def cleanup_timeouts(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=DELEGATION_TIMEOUT_SECONDS)
        specs = self.db.list_specs()
        cleaned = 0
        for s in specs:
            delegations = self.db.get_delegations_for_spec(s["id"])
            for d in delegations:
                if d.get("status") in ("pending", "in_progress"):
                    created = d.get("created_at", "")
                    if created and isinstance(created, str):
                        try:
                            created_dt = datetime.fromisoformat(created)
                        except (ValueError, TypeError):
                            created_dt = datetime.now(timezone.utc)
                        if created_dt.replace(tzinfo=timezone.utc) < cutoff:
                            self.db.update_delegation(d["id"], {"status": "timeout", "result": "Timed out"})
                            cleaned += 1
        return cleaned

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
