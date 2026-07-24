from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.domain.enums import PostCategory
from app.domain.platform_schemas import IngestionJob, KnowledgeDocument, StoredProviderProfile, UserSession
from app.domain.schemas import MemoryRecord, Post, PostCreate


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonRepository:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base = Path(base_dir or get_settings().data_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self.posts_path = self.base / "runtime_posts.json"
        self.docs_path = self.base / "runtime_docs.json"
        self.memories_path = self.base / "runtime_memories.json"
        self.traces_path = self.base / "runtime_traces.json"
        self.evals_path = self.base / "runtime_evals.json"
        self.knowledge_path = self.base / "runtime_knowledge.json"
        self.jobs_path = self.base / "runtime_ingestion_jobs.json"
        self.providers_path = self.base / "runtime_providers.json"
        self.sessions_path = self.base / "runtime_sessions.json"

    def load_posts(self) -> list[Post]:
        rows = self._read_json(self.posts_path, [])
        return [Post.model_validate(row) for row in rows]

    def save_posts(self, posts: list[Post]) -> None:
        self._write_json(self.posts_path, [post.model_dump(mode="json") for post in posts])

    def create_post(self, payload: PostCreate, author_alias: str = "匿名同学") -> Post:
        post = Post(
            **payload.model_dump(),
            post_id=f"post-{uuid.uuid4().hex[:10]}",
            author_alias=author_alias,
            created_at=now_iso(),
        )
        posts = self.load_posts()
        posts.insert(0, post)
        self.save_posts(posts)
        return post

    def find_post(self, post_id: str) -> Post | None:
        return next((post for post in self.load_posts() if post.post_id == post_id), None)

    def load_documents(self) -> list[dict[str, str]]:
        return self._read_json(self.docs_path, [])

    def save_documents(self, docs: list[dict[str, str]]) -> None:
        self._write_json(self.docs_path, docs)

    def load_knowledge(self) -> list[KnowledgeDocument]:
        return [KnowledgeDocument.model_validate(row) for row in self._read_json(self.knowledge_path, [])]

    def save_knowledge(self, document: KnowledgeDocument) -> KnowledgeDocument:
        rows = self.load_knowledge()
        rows = [row for row in rows if row.source_id != document.source_id]
        rows.insert(0, document)
        self._write_json(self.knowledge_path, [row.model_dump(mode="json") for row in rows])
        return document

    def delete_knowledge(self, source_id: str) -> bool:
        rows = self.load_knowledge()
        kept = [row for row in rows if row.source_id != source_id]
        self._write_json(self.knowledge_path, [row.model_dump(mode="json") for row in kept])
        return len(kept) != len(rows)

    def load_ingestion_jobs(self) -> list[IngestionJob]:
        return [IngestionJob.model_validate(row) for row in self._read_json(self.jobs_path, [])]

    def save_ingestion_job(self, job: IngestionJob) -> IngestionJob:
        rows = [row for row in self.load_ingestion_jobs() if row.job_id != job.job_id]
        rows.insert(0, job)
        self._write_json(self.jobs_path, [row.model_dump(mode="json") for row in rows[:200]])
        return job

    def find_ingestion_job(self, job_id: str) -> IngestionJob | None:
        return next((job for job in self.load_ingestion_jobs() if job.job_id == job_id), None)

    def load_provider_profiles(self) -> list[StoredProviderProfile]:
        return [StoredProviderProfile.model_validate(row) for row in self._read_json(self.providers_path, [])]

    def save_provider_profile(self, profile: StoredProviderProfile) -> StoredProviderProfile:
        rows = [row for row in self.load_provider_profiles() if row.provider_id != profile.provider_id]
        rows.insert(0, profile)
        self._write_json(self.providers_path, [row.model_dump(mode="json") for row in rows])
        return profile

    def delete_provider_profile(self, provider_id: str) -> bool:
        rows = self.load_provider_profiles()
        kept = [row for row in rows if row.provider_id != provider_id]
        self._write_json(self.providers_path, [row.model_dump(mode="json") for row in kept])
        return len(kept) != len(rows)

    def load_sessions(self, user_id: str | None = None) -> list[UserSession]:
        rows = [UserSession.model_validate(row) for row in self._read_json(self.sessions_path, [])]
        return [row for row in rows if user_id is None or row.user_id == user_id]

    def save_session(self, session: UserSession) -> UserSession:
        rows = [row for row in self.load_sessions() if row.session_id != session.session_id]
        rows.insert(0, session)
        self._write_json(self.sessions_path, [row.model_dump(mode="json") for row in rows[:500]])
        return session

    def delete_session(self, user_id: str, session_id: str) -> bool:
        rows = self.load_sessions()
        kept = [row for row in rows if not (row.user_id == user_id and row.session_id == session_id)]
        self._write_json(self.sessions_path, [row.model_dump(mode="json") for row in kept])
        return len(kept) != len(rows)

    def append_trace(self, trace: dict[str, Any]) -> None:
        traces = self._read_json(self.traces_path, [])
        traces.append(trace)
        self._write_json(self.traces_path, traces[-500:])

    def traces(self) -> list[dict[str, Any]]:
        return self._read_json(self.traces_path, [])

    def save_eval(self, run: dict[str, Any]) -> None:
        runs = self._read_json(self.evals_path, [])
        runs.insert(0, run)
        self._write_json(self.evals_path, runs[:50])

    def eval_runs(self) -> list[dict[str, Any]]:
        return self._read_json(self.evals_path, [])

    def load_memories(self, user_id: str) -> list[MemoryRecord]:
        rows = self._read_json(self.memories_path, [])
        return [MemoryRecord.model_validate(row) for row in rows if row.get("user_id") == user_id]

    def save_memory(self, memory: MemoryRecord) -> MemoryRecord:
        rows = self._read_json(self.memories_path, [])
        rows = [row for row in rows if row.get("memory_id") != memory.memory_id]
        rows.insert(0, memory.model_dump(mode="json"))
        self._write_json(self.memories_path, rows)
        return memory

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        rows = self._read_json(self.memories_path, [])
        kept = [row for row in rows if not (row.get("user_id") == user_id and row.get("memory_id") == memory_id)]
        self._write_json(self.memories_path, kept)
        return len(kept) != len(rows)

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, value: Any) -> None:
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)


def category_cycle(index: int) -> PostCategory:
    categories: list[PostCategory] = list(PostCategory)
    return categories[index % len(categories)]
