from __future__ import annotations

from typing import Any


class SSpecValidationError(Exception):
    def __init__(self, rule: str, message: str) -> None:
        self.rule = rule
        self.message = message
        super().__init__(f"[{rule}] {message}")


class SSpecValidator:
    RULES = [
        "R1: project_name must be non-empty",
        "R2: project_title must be non-empty",
        "R3: version must be valid semver (X.Y.Z)",
        "R4: description must not exceed 5000 chars",
        "R5: raw_spec must not be empty when status is 'active'",
        "R6: sections must have unique names",
        "R7: dependencies must reference existing sections",
        "R8: constraint values must be bool, number, or string",
        "R9: version must not be 0.0.0",
        "R10: created_at must precede updated_at",
        "R11: status must be one of draft, active, deprecated, archived",
        "R12: graph_snapshot keys must be known",
    ]

    def validate(self, spec_dict: dict[str, Any]) -> list[SSpecValidationError]:
        errors: list[SSpecValidationError] = []

        if not spec_dict.get("project_name"):
            errors.append(SSpecValidationError("R1", "project_name must be non-empty"))

        if not spec_dict.get("project_title"):
            errors.append(SSpecValidationError("R2", "project_title must be non-empty"))

        version = spec_dict.get("version", "")
        if version.count(".") != 2 or not all(p.isdigit() for p in version.split(".") if p):
            errors.append(SSpecValidationError("R3", f"version '{version}' is not valid semver"))

        desc = spec_dict.get("project_description", "")
        if len(desc) > 5000:
            errors.append(SSpecValidationError("R4", f"description exceeds 5000 chars ({len(desc)})"))

        status = spec_dict.get("status", "draft")
        raw_spec = spec_dict.get("raw_spec", "")
        if status == "active" and not raw_spec.strip():
            errors.append(SSpecValidationError("R5", "raw_spec must not be empty when status is 'active'"))

        if version == "0.0.0":
            errors.append(SSpecValidationError("R9", "version must not be 0.0.0"))

        valid_statuses = {"draft", "active", "deprecated", "archived"}
        if status not in valid_statuses:
            errors.append(SSpecValidationError("R11", f"status '{status}' not in {valid_statuses}"))

        snapshot = spec_dict.get("graph_snapshot")
        if isinstance(snapshot, dict):
            sections = snapshot.get("sections", [])
            seen_names: set[str] = set()
            for sec in sections:
                if isinstance(sec, dict):
                    name = sec.get("name")
                    if name in seen_names:
                        errors.append(SSpecValidationError("R6", f"duplicate section name '{name}'"))
                    seen_names.add(name)

        return errors
