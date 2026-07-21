from __future__ import annotations

from app.domain.schemas import Post
from app.retrieval.chunking import Chunk, chunk_text, chunks_from_documents


def chunks_from_posts(posts: list[Post]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for post in posts:
        body = f"{post.title}\n{post.body}\n标签:{','.join(post.tags)} 地点:{post.location or ''}"
        chunks.extend(
            chunk_text(
                source_id=post.post_id,
                source_type="post",
                title=post.title,
                text=body,
                official=False,
                metadata={
                    "category": post.category.value,
                    "location": post.location or "",
                    "created_at": post.created_at,
                },
                target_tokens=180,
                overlap=20,
            )
        )
    return chunks


def build_corpus(posts: list[Post], docs: list[dict[str, str]]) -> list[Chunk]:
    return chunks_from_documents(docs) + chunks_from_posts(posts)

