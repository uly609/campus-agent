git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
from __future__ import annotations

import base64
import hashlib
import uuid

import httpx
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.domain.platform_schemas import (
    ProviderProfile,
    ProviderProfileCreate,
    ProviderRole,
    StoredProviderProfile,
)
from app.services.repository import JsonRepository, now_iso


class ProviderRegistry:
    def __init__(
        self,
        repository: JsonRepository | None = None,
        encryption_secret: str | None = None,
    ) -> None:
        self.repository = repository or JsonRepository()
        secret = encryption_secret or get_settings().provider_encryption_secret
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
        self.cipher = Fernet(key)

    def list_public(self) -> list[ProviderProfile]:
        return [self._public(item) for item in self.repository.load_provider_profiles()]

    def create(self, payload: ProviderProfileCreate) -> ProviderProfile:
        timestamp = now_iso()
        stored = StoredProviderProfile(
            provider_id=f"provider-{uuid.uuid4().hex[:10]}",
            name=payload.name,
            role=payload.role,
            tier=payload.tier,
            base_url=payload.base_url.rstrip("/"),
            model=payload.model,
            enabled=payload.enabled,
            api_key_present=bool(payload.api_key),
            api_key_ciphertext=self._encrypt(payload.api_key),
            created_at=timestamp,
            updated_at=timestamp,
        )
        return self._public(self.repository.save_provider_profile(stored))

    def delete(self, provider_id: str) -> bool:
        return self.repository.delete_provider_profile(provider_id)

    def runtime_specs(self, role: ProviderRole) -> list[tuple[str, str, str, str | None]]:
        tier_order = {"local_primary": 0, "local_backup": 1, "cloud_fallback": 2}
        profiles = sorted(
            (
                profile
                for profile in self.repository.load_provider_profiles()
                if profile.enabled and profile.role == role
            ),
            key=lambda item: tier_order[item.tier],
        )
        return [
            (profile.name, profile.model, profile.base_url, self._decrypt(profile.api_key_ciphertext))
            for profile in profiles
        ]

    async def check(self, provider_id: str) -> ProviderProfile:
        stored = next(
            (
                profile
                for profile in self.repository.load_provider_profiles()
                if profile.provider_id == provider_id
            ),
            None,
        )
        if stored is None:
            raise KeyError("PROVIDER_NOT_FOUND")
        headers: dict[str, str] = {}
        api_key = self._decrypt(stored.api_key_ciphertext)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        status = "failed"
        try:
            endpoint = f"{stored.base_url.rstrip('/')}/models"
            if not stored.base_url.rstrip("/").endswith("/v1"):
                endpoint = f"{stored.base_url.rstrip('/')}/v1/models"
            async with httpx.AsyncClient(timeout=get_settings().provider_timeout_seconds) as client:
                response = await client.get(endpoint, headers=headers)
                response.raise_for_status()
            status = "healthy"
        except httpx.HTTPError:
            status = "failed"
        checked = stored.model_copy(
            update={"last_check_status": status, "last_check_at": now_iso(), "updated_at": now_iso()}
        )
        return self._public(self.repository.save_provider_profile(checked))

    def _encrypt(self, value: str | None) -> str | None:
        if not value:
            return None
        return self.cipher.encrypt(value.encode("utf-8")).decode("ascii")

    def _decrypt(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            return self.cipher.decrypt(value.encode("ascii")).decode("utf-8")
        except InvalidToken:
            return None

    @staticmethod
    def _public(stored: StoredProviderProfile) -> ProviderProfile:
        return ProviderProfile.model_validate(
            stored.model_dump(exclude={"api_key_ciphertext"})
        )
