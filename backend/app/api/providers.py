git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.domain.platform_schemas import ProviderProfile, ProviderProfileCreate
from app.services.provider_registry import ProviderRegistry

router = APIRouter(prefix="/api/v1/providers")
registry = ProviderRegistry()


@router.get("", response_model=list[ProviderProfile])
def list_providers() -> list[ProviderProfile]:
    return registry.list_public()


@router.post("", response_model=ProviderProfile, status_code=status.HTTP_201_CREATED)
def create_provider(payload: ProviderProfileCreate) -> ProviderProfile:
    return registry.create(payload)


@router.post("/{provider_id}/check", response_model=ProviderProfile)
async def check_provider(provider_id: str) -> ProviderProfile:
    try:
        return await registry.check(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"code": str(exc.args[0])}) from exc


@router.delete("/{provider_id}")
def delete_provider(provider_id: str) -> dict[str, object]:
    if not registry.delete(provider_id):
        raise HTTPException(status_code=404, detail={"code": "PROVIDER_NOT_FOUND"})
    return {"deleted": True, "provider_id": provider_id}
