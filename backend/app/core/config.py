from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = Field(default="local", alias="CAMPUSFLOW_ENV")
    demo_token: str = Field(default="demo-token", alias="CAMPUSFLOW_DEMO_TOKEN")
    database_url: str = "sqlite:///data/generated/campusflow.db"
    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "campusflow-password"
    openai_api_key: Optional[str] = None
    local_primary_chat_url: Optional[str] = None
    local_backup_chat_url: Optional[str] = None
    cloud_fallback_chat_url: Optional[str] = None
    vlm_api_key: Optional[str] = None
    provider_timeout_seconds: float = 8.0
    provider_max_retries: int = 2
    memory_enabled: bool = True
    data_dir: str = "data/generated"
    prompt_version: str = "campusflow-agent-v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()

