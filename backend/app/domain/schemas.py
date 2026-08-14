from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

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
    domain: str = Field(default="enterprise", min_length=2, max_length=40)


class Post(PostCreate):
    post_id: str
    author_alias: str
    created_at: str
    comment_count: int = Field(default=0, ge=0)


class PostCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=600)

    @field_validator("body")
    @classmethod
    def normalize_body(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("comment body cannot be blank")
        return normalized


class PostComment(PostCommentCreate):
    comment_id: str
    post_id: str
    author_alias: str
    created_at: str


class PostReactionCreate(BaseModel):
    user_id: str = Field(default="demo-user", min_length=1, max_length=80)
    liked: bool = True


class PostReaction(PostReactionCreate):
    post_id: str
    updated_at: str


class FeedPost(Post):
    like_count: int = Field(default=0, ge=0)
    report_count: int = Field(default=0, ge=0)
    viewer_liked: bool = False
    ranking_score: float = 0
    ranking_reason: str = "按发布时间排序"


class PostReportCreate(BaseModel):
    user_id: str = Field(default="demo-user", min_length=1, max_length=80)
    reason: Literal["spam", "abuse", "fraud", "privacy", "inaccurate", "other"]
    detail: str = Field(default="", max_length=500)


class PostReport(PostReportCreate):
    report_id: str
    post_id: str
    risk_score: float = Field(ge=0, le=1)
    suggested_decision: Literal["keep", "review", "hide"]
    status: Literal["pending_review", "resolved"] = "pending_review"
    final_decision: Literal["keep", "hide"] | None = None
    reviewer_alias: str | None = None
    review_note: str = ""
    created_at: str
    resolved_at: str | None = None


class ModerationReviewCreate(BaseModel):
    decision: Literal["keep", "hide"]
    reviewer_alias: str = Field(default="社区管理员", min_length=1, max_length=80)
    note: str = Field(default="", max_length=500)


class CommunityAuditEvent(BaseModel):
    event_id: str
    action: Literal["report_created", "report_reviewed"]
    actor_alias: str
    post_id: str
    report_id: str
    detail: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class Evidence(BaseModel):
    evidence_id: str
    source_id: str
    source_type: Literal["official", "post", "event", "image", "skill", "external", "profile"]
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
    quoted_span: str = ""


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


class ChatFileUpload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    data_url: str = Field(min_length=10, max_length=14_100_000)

    @model_validator(mode="after")
    def validate_file(self) -> "ChatFileUpload":
        suffix = self.name.lower().rsplit(".", 1)[-1] if "." in self.name else ""
        if suffix not in {"xlsx", "csv", "pdf", "txt", "md", "markdown"}:
            raise ValueError("chat file type is not supported")
        if not self.data_url.startswith("data:") or ";base64," not in self.data_url[:160]:
            raise ValueError("chat files must use base64 data URLs")
        return self


class ChatRequest(BaseModel):
    session_id: str = "demo-session"
    user_id: str = "demo-user"
    message: str = Field(min_length=1, max_length=2000)
    image_urls: list[str] = Field(default_factory=list, max_length=4)
    files: list[ChatFileUpload] = Field(default_factory=list, max_length=4)
    is_agent: bool = False

    @model_validator(mode="after")
    def validate_total_file_size(self) -> "ChatRequest":
        if sum(len(item.data_url) for item in self.files) > 28_000_000:
            raise ValueError("chat files must be at most 20 MB in total")
        return self

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, values: list[str]) -> list[str]:
        allowed_data_prefixes = (
            "data:image/jpeg;base64,",
            "data:image/png;base64,",
            "data:image/webp;base64,",
        )
        for value in values:
            if len(value) > 3_000_000:
                raise ValueError("each chat image must be at most 3 MB")
            if not value.startswith(("https://", *allowed_data_prefixes)):
                raise ValueError("chat images must use HTTPS or supported image data URLs")
        return values


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
