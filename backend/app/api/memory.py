from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.memory.consumer import MemoryConsumer
from app.memory.repository import MemoryRepository

router = APIRouter(prefix="/api/v1")
repository = MemoryRepository()


@router.get("/memories")
def list_memories(user_id: str = "demo-user") -> dict[str, object]:
    processed = MemoryConsumer(repository).consume_available()
    return {"processed_events": processed, "memories": [item.model_dump() for item in repository.list_user(user_id)]}


@router.delete("/memories/{memory_id}")
def delete_memory(memory_id: str, user_id: str = "demo-user") -> dict[str, object]:
    deleted = repository.delete(user_id, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": "MEMORY_NOT_FOUND"})
    return {"deleted": True, "memory_id": memory_id}

