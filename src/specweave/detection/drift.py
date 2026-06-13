from __future__ import annotations

from typing import Any

from specweave.detection.models import Drift
from specweave.persistence import SQLiteStore
from specweave.spec_format.diff import detect_drift


class DriftDetector:
    def __init__(self, db: SQLiteStore) -> None:
        self.db = db

    def detect_drift(self, spec_id: str, baseline: str | None = None) -> list[Drift]:
        spec_data = self.db.get_spec(spec_id)
        if spec_data is None:
            return []

        if baseline is not None:
            baseline_data = self.db.get_spec(baseline)
            if baseline_data is None:
                return []
        else:
            specs = self.db.list_specs()
            previous = None
            for s in specs:
                if s["id"] == spec_id:
                    continue
                if s.get("project_name") == spec_data.get("project_name"):
                    if previous is None or s.get("created_at", "") > previous.get("created_at", ""):
                        previous = s
            if previous is None:
                return []
            baseline_data = previous

        drift_map = detect_drift(spec_data, baseline_data)
        drifts: list[Drift] = []
        for field, change in drift_map.items():
            drift_score = 0.0
            old_val = str(change.get("from", ""))
            new_val = str(change.get("to", ""))
            if old_val and new_val:
                common = sum(1 for a, b in zip(old_val, new_val) if a == b)
                max_len = max(len(old_val), len(new_val))
                drift_score = 1.0 - (common / max_len) if max_len > 0 else 0.0

            drifts.append(Drift(
                spec_id=spec_id,
                field=field,
                baseline_value=change.get("from"),
                current_value=change.get("to"),
                drift_score=drift_score,
            ))

        return drifts
