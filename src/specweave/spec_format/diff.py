from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


def semantic_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    all_keys = set(old.keys()) | set(new.keys())
    for key in all_keys:
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}
    return changes


def text_diff(old_text: str, new_text: str) -> list[dict[str, Any]]:
    matcher = SequenceMatcher(None, old_text, new_text)
    changes: list[dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            changes.append({
                "type": "replace",
                "old": {"start": i1, "end": i2, "text": old_text[i1:i2]},
                "new": {"start": j1, "end": j2, "text": new_text[j1:j2]},
            })
        elif tag == "delete":
            changes.append({
                "type": "delete",
                "old": {"start": i1, "end": i2, "text": old_text[i1:i2]},
                "new": None,
            })
        elif tag == "insert":
            changes.append({
                "type": "insert",
                "old": None,
                "new": {"start": j1, "end": j2, "text": new_text[j1:j2]},
            })
    return changes


def detect_drift(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    drift: dict[str, Any] = {}
    for key in ("project_name", "project_title", "project_description", "version", "raw_spec"):
        if key in current and key in previous:
            if current[key] != previous[key]:
                drift[key] = {"from": previous[key], "to": current[key]}
    return drift
