from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from app.core.config import get_settings
from app.retrieval.chunking import Chunk
from app.retrieval.embeddings import cosine
from app.retrieval.graph_rag import extract_entities


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
            if records:
                dimensions = len(records[0].embedding)
                session.run(
                    f"""
                    CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
                    FOR (c:Chunk) ON (c.embedding)
                    OPTIONS {{indexConfig: {{
                      `vector.dimensions`: {dimensions},
                      `vector.similarity_function`: 'cosine'
                    }}}}
                    """
                ).consume()
            for record in records:
                session.run(
                    """
                    MERGE (c:Chunk {chunk_id: $chunk_id})
                    SET c.source_id = $source_id,
                        c.title = $title,
                        c.text = $text,
                        c.official = $official,
                        c.source_type = $source_type,
                        c.metadata_json = $metadata_json,
                        c.embedding = $embedding
                    """,
                    chunk_id=record.chunk.chunk_id,
                    source_id=record.chunk.source_id,
                    title=record.chunk.title,
                    text=record.chunk.text,
                    official=record.chunk.official,
                    source_type=record.chunk.source_type,
                    metadata_json=json.dumps(record.chunk.metadata, ensure_ascii=False),
                    embedding=record.embedding,
                )

    def upsert_graph(self) -> None:
        if not self._driver:
            return
        by_source: dict[str, Chunk] = {}
        for record in self.records:
            by_source.setdefault(record.chunk.source_id, record.chunk)
        with self._driver.session() as session:
            session.run("CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.source_id IS UNIQUE").consume()
            session.run("CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE").consume()
            for source_id, chunk in by_source.items():
                entities = extract_entities(f"{chunk.title} {chunk.text}")
                session.run(
                    """
                    MERGE (s:Source {source_id: $source_id})
                    SET s.title = $title
                    WITH s
                    UNWIND $entities AS entity_name
                    MERGE (e:Entity {name: entity_name})
                    MERGE (s)-[:MENTIONS]->(e)
                    """,
                    source_id=source_id,
                    title=chunk.title,
                    entities=entities,
                ).consume()

    def vector_search(self, query_embedding: list[float], top_k: int = 40) -> list[tuple[Chunk, float]]:
        if self._driver:
            try:
                with self._driver.session() as session:
                    records = session.run(
                        """
                        CALL db.index.vector.queryNodes('chunk_embedding', $top_k, $embedding)
                        YIELD node, score
                        RETURN node.chunk_id AS chunk_id, score
                        ORDER BY score DESC
                        """,
                        top_k=top_k,
                        embedding=query_embedding,
                    )
                    by_chunk = {record.chunk.chunk_id: record.chunk for record in self.records}
                    results = [
                        (by_chunk[row["chunk_id"]], float(row["score"]))
                        for row in records
                        if row["chunk_id"] in by_chunk
                    ]
                    if results:
                        return results
            except Exception as exc:
                self.degraded_reason = f"neo4j_vector_query_failed:{exc.__class__.__name__}"
        scored = [(record.chunk, cosine(query_embedding, record.embedding)) for record in self.records]
        return [(chunk, score) for chunk, score in sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]]

    def graph_search(self, query_entities: list[str], top_k: int = 20) -> list[tuple[Chunk, float]]:
        if not self._driver or not query_entities:
            return []
        try:
            with self._driver.session() as session:
                records = session.run(
                    """
                    CALL () {
                      MATCH (s:Source)-[:MENTIONS]->(e:Entity)
                      WHERE e.name IN $entities
                      RETURN s.source_id AS source_id, 1.0 AS weight
                      UNION ALL
                      MATCH (:Entity)<-[:MENTIONS]-(origin:Source)-[:MENTIONS]->(bridge:Entity)<-[:MENTIONS]-(s:Source)
                      WHERE bridge.name IN $entities AND s <> origin
                      RETURN s.source_id AS source_id, 0.35 AS weight
                    }
                    RETURN source_id, sum(weight) AS score
                    ORDER BY score DESC
                    LIMIT $top_k
                    """,
                    entities=query_entities,
                    top_k=top_k,
                )
                by_source = {record.chunk.source_id: record.chunk for record in self.records}
                return [
                    (by_source[row["source_id"]], float(row["score"]))
                    for row in records
                    if row["source_id"] in by_source
                ]
        except Exception as exc:
            self.degraded_reason = f"neo4j_graph_query_failed:{exc.__class__.__name__}"
            return []
