from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.retrieval.chunking import Chunk
from app.retrieval.embeddings import cosine


@dataclass
class VectorRecord:
    chunk: Chunk
    embedding: list[float]


class Neo4jVectorStore:
    def __init__(self) -> None:
        self.records: list[VectorRecord] = []
        self.degraded_reason = ""
        self._driver: Any = None
        settings = get_settings()
        try:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                connection_timeout=1,
            )
            with self._driver.session() as session:
                session.run("RETURN 1").consume()
        except (ImportError, OSError, Exception) as exc:
            self.degraded_reason = f"neo4j_unavailable:{exc.__class__.__name__}"
            self._driver = None

    def upsert_chunks(self, records: list[VectorRecord]) -> None:
        self.records = records
        if not self._driver:
            return
        with self._driver.session() as session:
            session.run(
                """
                CREATE CONSTRAINT chunk_id IF NOT EXISTS
                FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
                """
            )
            for record in records:
                session.run(
                    """
                    MERGE (c:Chunk {chunk_id: $chunk_id})
                    SET c.source_id = $source_id,
                        c.title = $title,
                        c.text = $text,
                        c.official = $official,
                        c.embedding = $embedding
                    """,
                    chunk_id=record.chunk.chunk_id,
                    source_id=record.chunk.source_id,
                    title=record.chunk.title,
                    text=record.chunk.text,
                    official=record.chunk.official,
                    embedding=record.embedding,
                )

    def vector_search(self, query_embedding: list[float], top_k: int = 40) -> list[tuple[Chunk, float]]:
        scored = [(record.chunk, cosine(query_embedding, record.embedding)) for record in self.records]
        return [(chunk, score) for chunk, score in sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]]

