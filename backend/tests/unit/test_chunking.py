from __future__ import annotations

from app.retrieval.chunking import chunk_text, tokenize


def test_chunking_keeps_metadata_and_overlap() -> None:
    text = " ".join(f"词{i}" for i in range(620))
    chunks = chunk_text("doc-1", "official", "标题", text, True, {"path": "doc.md"}, target_tokens=100, overlap=20)
    assert len(chunks) > 1
    assert chunks[0].source_id == "doc-1"
    assert chunks[0].metadata["path"] == "doc.md"
    assert len(tokenize(chunks[1].text)) <= 100

