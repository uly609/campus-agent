from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source_id: str
    source_type: str
    title: str
    text: str
    official: bool
    metadata: dict[str, str]


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for segment in re.findall(r"[a-z0-9_\u4e00-\u9fff]+", text.lower()):
        if not re.fullmatch(r"[\u4e00-\u9fff]+", segment):
            tokens.append(segment)
            continue
        tokens.append(segment)
        for width in (2, 3):
            tokens.extend(segment[index : index + width] for index in range(len(segment) - width + 1))
    return tokens


def chunk_text(
    source_id: str,
    source_type: str,
    title: str,
    text: str,
    official: bool,
    metadata: dict[str, str] | None = None,
    target_tokens: int = 500,
    overlap: int = 80,
) -> list[Chunk]:
    words = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    if not words:
        return []
    if len(words) <= target_tokens:
        return [
            Chunk(
                chunk_id=f"{source_id}:0",
                source_id=source_id,
                source_type=source_type,
                title=title,
                text=text.strip(),
                official=official,
                metadata=metadata or {},
            )
        ]
    chunks: list[Chunk] = []
    start = 0
    index = 0
    step = max(1, target_tokens - overlap)
    while start < len(words):
        window = words[start : start + target_tokens]
        chunks.append(
            Chunk(
                chunk_id=f"{source_id}:{index}",
                source_id=source_id,
                source_type=source_type,
                title=title,
                text=" ".join(window),
                official=official,
                metadata=metadata or {},
            )
        )
        start += step
        index += 1
    return chunks


def chunks_from_documents(documents: Iterable[dict[str, str]]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in documents:
        chunks.extend(
            chunk_text(
                source_id=doc["source_id"],
                source_type=doc.get("source_type", "official"),
                title=doc["title"],
                text=doc["body"],
                official=doc.get("official", "true") == "true",
                metadata={"path": doc.get("path", ""), "url": doc.get("url", "")},
            )
        )
    return chunks
