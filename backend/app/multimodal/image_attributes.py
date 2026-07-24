from __future__ import annotations

from typing import Any

from app.llm.router import ProviderRouter


_ZH_VALUES = {
    "water bottle": "水杯",
    "bottle": "水杯",
    "campus card": "校园卡",
    "student card": "校园卡",
    "backpack": "背包",
    "umbrella": "雨伞",
    "headphones": "耳机",
    "keys": "钥匙",
    "phone": "手机",
    "blue": "蓝色",
    "black": "黑色",
    "white": "白色",
    "red": "红色",
    "green": "绿色",
    "gray": "灰色",
    "grey": "灰色",
    "stainless steel": "不锈钢",
    "plastic": "塑料",
    "metal": "金属",
    "fabric": "布料",
    "leather": "皮革",
    "library": "图书馆",
    "outdoor seating area": "室外休息区",
    "modern building": "教学楼附近",
    "student service center": "学生服务中心",
    "canteen": "食堂",
    "gym": "体育馆",
}


def normalize_image_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(attributes)
    for key in ("category", "color", "brand", "material"):
        value = normalized.get(key)
        if isinstance(value, str):
            normalized[key] = _ZH_VALUES.get(value.strip().lower(), value.strip())
    hints = normalized.get("location_hints")
    if isinstance(hints, str):
        hints = [hints]
    if isinstance(hints, list):
        normalized["location_hints"] = [
            _ZH_VALUES.get(str(hint).strip().lower(), str(hint).strip())
            for hint in hints[:3]
            if str(hint).strip()
        ]
    return normalized


async def extract_image_attributes(image_url: str, router: ProviderRouter | None = None) -> dict[str, Any]:
    active_router = router or ProviderRouter()
    result = await active_router.analyze_image(
        image_url,
        "提取失物招领属性、地点提示、可见文字和安全标记，所有描述性字段使用简体中文。",
    )
    if isinstance(result.content, dict):
        return normalize_image_attributes(dict(result.content))
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
