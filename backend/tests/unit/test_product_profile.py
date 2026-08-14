from fastapi.testclient import TestClient

from app.main import app


def test_product_profile_exposes_enterprise_knowledge_community_brand() -> None:
    response = TestClient(app).get("/api/v1/profile")

    assert response.status_code == 200
    assert response.json() == {
        "key": "enterprise_knowledge_community",
        "brand": "AtlasHub AI",
        "short_name": "AtlasHub",
        "subtitle": "企业知识社区与智能治理 Agent",
        "community_label": "知识社区",
        "knowledge_label": "企业知识库",
    }
