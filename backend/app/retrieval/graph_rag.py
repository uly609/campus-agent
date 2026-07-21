from __future__ import annotations

from collections import defaultdict

from app.retrieval.chunking import Chunk, tokenize


class GraphRAG:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.entity_to_sources: defaultdict[str, set[str]] = defaultdict(set)
        self.source_to_entities: defaultdict[str, set[str]] = defaultdict(set)
        for chunk in chunks:
            for entity in extract_entities(chunk.text + " " + chunk.title):
                self.entity_to_sources[entity].add(chunk.source_id)
                self.source_to_entities[chunk.source_id].add(entity)

    def expand(self, query: str, top_k: int = 20) -> list[tuple[Chunk, float]]:
        query_entities = extract_entities(query)
        candidate_ids: defaultdict[str, float] = defaultdict(float)
        for entity in query_entities:
            for source_id in self.entity_to_sources.get(entity, set()):
                candidate_ids[source_id] += 1.0
                for neighbor in self.source_to_entities[source_id]:
                    if neighbor == entity:
                        continue
                    for two_hop_source in self.entity_to_sources.get(neighbor, set()):
                        candidate_ids[two_hop_source] += 0.35
        by_source = {chunk.source_id: chunk for chunk in self.chunks}
        ranked = [
            (by_source[source_id], score)
            for source_id, score in candidate_ids.items()
            if source_id in by_source and score > 0
        ]
        return sorted(ranked, key=lambda item: item[1], reverse=True)[:top_k]

    def visualization(self) -> dict[str, list[dict[str, str]]]:
        nodes = [{"id": source_id, "type": "source"} for source_id in self.source_to_entities]
        nodes.extend({"id": entity, "type": "entity"} for entity in self.entity_to_sources)
        edges: list[dict[str, str]] = []
        for source_id, entities in self.source_to_entities.items():
            edges.extend({"source": source_id, "target": entity, "type": "MENTIONS"} for entity in entities)
        return {"nodes": nodes, "edges": edges}


def extract_entities(text: str) -> list[str]:
    tokens = tokenize(text)
    entities = []
    keywords = {
        "图书馆",
        "宿舍",
        "食堂",
        "教务处",
        "体育馆",
        "校医院",
        "北门",
        "南门",
        "失物",
        "一卡通",
        "研究生院",
        "奖学金",
    }
    for token in tokens:
        if token in keywords or len(token) >= 4:
            entities.append(token)
    return sorted(set(entities))
