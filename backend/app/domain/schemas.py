from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import Intent, MemoryType, PostCategory


class ErrorInfo(BaseModel):
    code: str
    message: str
    retryable: bool = False


class PostImage(BaseModel):
    image_id: str
    url: str
    alt_text: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)


class PostCreate(BaseModel):
    title: str = Field(min_length=2, max_length=80)
    body: str = Field(min_length=2, max_length=2000)
    category: PostCategory
    tags: list[str] = Field(default_factory=list, max_length=8)
    location: Optional[str] = Field(default=None, max_length=80)
    images: list[PostImage] = Field(default_factory=list, max_length=4)


class Post(PostCreate):
    post_id: str
    author_alias: str
    created_at: str


class Evidence(BaseModel):
    evidence_id: str
    source_id: str
    source_type: Literal["official", "post", "event", "image"]
    title: str
    excerpt: str
    score: float = Field(ge=0)
    official: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    citation_id: str
    claim_id: str
    evidence_id: str
    source_id: str
    title: str


class Claim(BaseModel):
    claim_id: str
    text: str
    evidence_ids: list[str]

    @field_validator("evidence_ids")
    @classmethod
    def factual_claims_need_evidence(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("FACTUAL_CLAIM_WITHOUT_EVIDENCE")
        return value


class GroundedAnswer(BaseModel):
    answer: str
    claims: list[Claim] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    unsupported_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: list[dict[str, Any]] | dict[str, Any] | None
    error_code: Optional[str]
    error_message: Optional[str]
    latency_ms: int
    provenance: list[dict[str, Any]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str = "demo-session"
    user_id: str = "demo-user"
    message: str = Field(min_length=1, max_length=2000)
    image_urls: list[str] = Field(default_factory=list, max_length=4)


class ChatResponse(BaseModel):
    request_id: str
    answer: GroundedAnswer
    intent: Intent
    citations: list[Citation]
    trace: list[dict[str, Any]]
    degraded_mode: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    image_attributes: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=8, ge=1, le=12)


class MemoryRecord(BaseModel):
    memory_id: str
    user_id: str
    memory_type: MemoryType
    key: str
    value: str
    hash_value: str
    embedding: list[float] = Field(default_factory=list)
    supersedes: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: str


class EvalRun(BaseModel):
    run_id: str
    created_at: str
    metrics: dict[str, float]
    report_path: str

