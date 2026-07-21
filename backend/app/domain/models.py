from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PostModel(Base):
    __tablename__ = "posts"

    post_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    location: Mapped[str | None] = mapped_column(String(80))
    author_alias: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    images: Mapped[list["PostImageModel"]] = relationship(back_populates="post")


class PostImageModel(Base):
    __tablename__ = "post_images"

    image_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.post_id"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_text: Mapped[str] = mapped_column(String(300), default="")
    attributes: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    post: Mapped[PostModel] = relationship(back_populates="images")


class UserSessionModel(Base):
    __tablename__ = "user_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class MemoryModel(Base):
    __tablename__ = "memories"

    memory_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    memory_type: Mapped[str] = mapped_column(String(32))
    key: Mapped[str] = mapped_column(String(120))
    value: Mapped[str] = mapped_column(Text)
    hash_value: Mapped[str] = mapped_column(String(128), index=True)
    embedding: Mapped[list[float]] = mapped_column(JSON, default=list)
    supersedes: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[str] = mapped_column(String(40))


class EvalRunModel(Base):
    __tablename__ = "eval_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    metrics: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    report_path: Mapped[str] = mapped_column(String(300), nullable=False)


class TraceModel(Base):
    __tablename__ = "traces"

    trace_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    node_name: Mapped[str] = mapped_column(String(80))
    latency_ms: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24))
    payload: Mapped[dict[str, str | int | float | bool]] = mapped_column(JSON, default=dict)

