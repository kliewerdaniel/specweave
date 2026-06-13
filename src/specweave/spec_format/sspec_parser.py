from __future__ import annotations

import json
from typing import Any

import yaml

from specweave.models.spec import Spec


class SSpecParseError(Exception):
    pass


class SSpecParser:
    @staticmethod
    def parse_yaml(content: str) -> Spec:
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise SSpecParseError(f"Invalid YAML: {e}") from e
        if not isinstance(data, dict):
            raise SSpecParseError("Root must be a mapping")
        if "project" not in data:
            raise SSpecParseError("Missing required 'project' key")
        project = data["project"]
        if not isinstance(project, dict):
            raise SSpecParseError("'project' must be a mapping")
        spec_id = data.get("id", "")
        spec = Spec(
            id=spec_id,
            project_name=project.get("name", ""),
            project_title=project.get("title", ""),
            project_description=data.get("description", ""),
            version=project.get("version", "0.1.0"),
            raw_spec=content,
        )
        spec.graph_snapshot = {
            "sections": data.get("sections", []),
            "dependencies": data.get("dependencies", []),
            "constraints": data.get("constraints", []),
            "metadata": data.get("metadata", {}),
        }
        return spec

    @staticmethod
    def parse_json(content: str) -> Spec:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise SSpecParseError(f"Invalid JSON: {e}") from e
        return SSpecParser._from_dict(data)

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> Spec:
        project = data.get("project", {})
        spec_id = data.get("id", "")
        spec = Spec(
            id=spec_id,
            project_name=project.get("name", ""),
            project_title=project.get("title", ""),
            project_description=data.get("description", ""),
            version=project.get("version", "0.1.0"),
            raw_spec=json.dumps(data, indent=2),
        )
        spec.graph_snapshot = {
            "sections": data.get("sections", []),
            "dependencies": data.get("dependencies", []),
            "constraints": data.get("constraints", []),
            "metadata": data.get("metadata", {}),
        }
        return spec

    @staticmethod
    def to_sspec_yaml(spec: Spec) -> str:
        data = {
            "id": spec.id,
            "project": {
                "name": spec.project_name,
                "title": spec.project_title,
                "version": spec.version,
            },
            "description": spec.project_description,
        }
        if spec.graph_snapshot:
            data["sections"] = spec.graph_snapshot.get("sections", [])
            data["dependencies"] = spec.graph_snapshot.get("dependencies", [])
            data["constraints"] = spec.graph_snapshot.get("constraints", [])
            data["metadata"] = spec.graph_snapshot.get("metadata", {})
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
