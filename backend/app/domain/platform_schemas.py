from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


KnowledgeStatus = Literal["queued", "indexing", "ready", "failed"]
JobStatus = Literal["queued", "processing", "completed", "failed"]
ProviderRole = Literal["chat", "embedding", "vlm"]
ProviderTier = Literal["local_primary", "local_backup", "cloud_fallback"]


class KnowledgeDocumentCreate(BaseModel):
    source_id: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=160)
    body: str = Field(min_length=2, max_length=200_000)
    source_type: Literal["official", "post"] = "official"
    official: bool = True
    path: str = Field(default="", max_length=500)
    url: str = Field(default="", max_length=1000)


class KnowledgeDocument(KnowledgeDocumentCreate):
    status: KnowledgeStatus
    content_hash: str
    chunk_count: int = 0
    created_at: str
    updated_at: str
    error_code: Optional[str] = None


class IngestionJob(BaseModel):
    job_id: str
    source_id: str
    status: JobStatus
    progress: int = Field(default=0, ge=0, le=100)
    attempt: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1, le=5)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class ProviderProfileCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    role: ProviderRole
    tier: ProviderTier
    base_url: str = Field(min_length=8, max_length=500)
    model: str = Field(min_length=1, max_length=120)
    api_key: Optional[str] = Field(default=None, min_length=8, max_length=500)
    enabled: bool = True


class ProviderProfile(BaseModel):
    provider_id: str
    name: str
    role: ProviderRole
    tier: ProviderTier
    base_url: str
    model: str
    enabled: bool
    api_key_present: bool
    last_check_status: Literal["unchecked", "healthy", "failed"] = "unchecked"
    last_check_at: Optional[str] = None
    created_at: str
    updated_at: str


class StoredProviderProfile(ProviderProfile):
    api_key_ciphertext: Optional[str] = None


class UserSession(BaseModel):
    session_id: str
    user_id: str
    title: str
    message_count: int = 0
    created_at: str
    updated_at: str
