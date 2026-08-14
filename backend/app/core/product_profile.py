from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductProfile:
    key: str
    brand: str
    short_name: str
    subtitle: str
    community_label: str
    knowledge_label: str


# The implementation keeps legacy campus adapters available for fixtures and
# migration tests, while the user-facing product is now enterprise knowledge.
ENTERPRISE_PROFILE = ProductProfile(
    key="enterprise_knowledge_community",
    brand="AtlasHub AI",
    short_name="AtlasHub",
    subtitle="企业知识社区与智能治理 Agent",
    community_label="知识社区",
    knowledge_label="企业知识库",
)


def get_product_profile() -> ProductProfile:
    return ENTERPRISE_PROFILE
