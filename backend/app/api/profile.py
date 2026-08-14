from fastapi import APIRouter

from app.core.product_profile import get_product_profile

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("")
def profile() -> dict[str, str]:
    current = get_product_profile()
    return {
        "key": current.key,
        "brand": current.brand,
        "short_name": current.short_name,
        "subtitle": current.subtitle,
        "community_label": current.community_label,
        "knowledge_label": current.knowledge_label,
    }
