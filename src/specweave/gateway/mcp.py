from __future__ import annotations

from typing import Any

from specweave.persistence import SQLiteStore


class MCPHandler:
    def __init__(self, db: SQLiteStore) -> None:
        self.db = db
        self._tools: dict[str, dict[str, Any]] = {
            "list_specs": {
                "name": "list_specs",
                "description": "List all specs with their status and version",
                "parameters": {"type": "object", "properties": {}},
            },
            "get_spec": {
                "name": "get_spec",
                "description": "Get a spec by ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "spec_id": {"type": "string", "description": "The spec ID"},
                    },
                    "required": ["spec_id"],
                },
            },
            "search_specs": {
                "name": "search_specs",
                "description": "Semantic search across all specs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
            },
            "get_gates": {
                "name": "get_gates",
                "description": "Get verification gate status for a spec",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "spec_id": {"type": "string", "description": "The spec ID"},
                    },
                    "required": ["spec_id"],
                },
            },
            "impact_analysis": {
                "name": "impact_analysis",
                "description": "Analyze impact of changing a spec",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "spec_id": {"type": "string", "description": "The spec ID"},
                    },
                    "required": ["spec_id"],
                },
            },
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools.values())

    def execute(self, tool: str, params: dict[str, Any]) -> Any:
        if tool not in self._tools:
            raise ValueError(f"Unknown tool: {tool}")
        handlers = {
            "list_specs": lambda p: self.db.list_specs(),
            "get_spec": lambda p: self.db.get_spec(p.get("spec_id", "")),
            "search_specs": lambda p: {"message": "Use vector store search endpoint"},
            "get_gates": lambda p: self.db.get_gates_for_spec(p.get("spec_id", "")),
            "impact_analysis": lambda p: {
                "target": p.get("spec_id", ""),
                "message": "Use A2A impact analysis endpoint",
            },
        }
        handler = handlers.get(tool)
        if handler is None:
            raise ValueError(f"No handler for tool: {tool}")
        return handler(params)
