from __future__ import annotations

from typing import Any

import chromadb

from specweave.config import settings


class VectorStore:
    def __init__(self, path: str) -> None:
        self.client = chromadb.PersistentClient(path=path)
        self._collections: dict[str, chromadb.Collection] = {}

    def get_or_create_collection(self, name: str = "specs") -> chromadb.Collection:
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    def add_document(self, doc_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        collection = self.get_or_create_collection()
        collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id],
        )

    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        collection = self.get_or_create_collection()
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        output = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                output.append({
                    "document": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                })
        return output

    def delete_document(self, doc_id: str) -> None:
        collection = self.get_or_create_collection()
        collection.delete(ids=[doc_id])

    def count(self) -> int:
        collection = self.get_or_create_collection()
        return collection.count()
