from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_GRAMMAR_DIR = Path(__file__).parent
_GRAMMAR_CACHE: dict[str, str] = {}


def load_grammar(name: str) -> str | None:
    if name in _GRAMMAR_CACHE:
        return _GRAMMAR_CACHE[name]
    path = _GRAMMAR_DIR / name
    if not path.exists():
        logger.warning("Grammar file not found: %s", path)
        return None
    content = path.read_text()
    _GRAMMAR_CACHE[name] = content
    return content


def validate_with_grammar(text: str, grammar_name: str) -> dict[str, Any]:
    grammar = load_grammar(grammar_name)
    if grammar is None:
        return {"valid": False, "error": f"Grammar {grammar_name} not found"}
    try:
        json.loads(text)
        return {"valid": True, "error": None}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": str(e)}


def get_available_grammars() -> list[str]:
    if not _GRAMMAR_DIR.exists():
        return []
    return [f.name for f in _GRAMMAR_DIR.iterdir() if f.suffix == ".gbnf"]
