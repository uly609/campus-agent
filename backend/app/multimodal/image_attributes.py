from __future__ import annotations

from typing import Any

from app.llm.router import ProviderRouter


async def extract_image_attributes(image_url: str, router: ProviderRouter | None = None) -> dict[str, Any]:
    active_router = router or ProviderRouter()
    result = await active_router.analyze_image(
        image_url,
        "Extract lost-and-found attributes, location hints, visible text, and safety flags.",
    )
    if isinstance(result.content, dict):
        return dict(result.content)
    return {}


def enhance_query_with_image(query: str, attributes: dict[str, Any]) -> str:
    pieces = [query]
    for key in ("category", "color", "brand", "material"):
        value = attributes.get(key)
        if value:
            pieces.append(str(value))
    for hint in attributes.get("location_hints", []):
        pieces.append(str(hint))
    return " ".join(pieces)
