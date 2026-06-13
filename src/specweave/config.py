from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SpecWeave"
    app_version: str = "2.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    ollama_host: str = "http://localhost:11434"
    ollama_timeout: int = 120

    speculator_model: str = "qwen2.5-3b"
    verifier_model: str = "nemotron-cascade-2-30b"
    general_model: str = "llama3.2-8b"
    embedding_model: str = "nomic-embed-text"

    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    data_dir: Path = Path(".sovereignspec")
    sqlite_path: Path = Path(".sovereignspec/memory/specweave.db")
    chroma_path: str = ".sovereignspec/memory/chromadb"

    model_config = {"env_prefix": "SPECWEAVE_", "frozen": False}


settings = Settings()
