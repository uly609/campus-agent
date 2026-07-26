from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from scripts.seed import main as seed_main


def test_demo_flows_cover_chat_search_draft_memory_eval() -> None:
    seed_main()
    client = TestClient(app)
    chat = client.post("/api/v1/chat", json={"message": "图书馆今天几点关门？"}).json()
    assert chat["citations"]
    search = client.post("/api/v1/posts/search", json={"query": "南门 校园卡", "top_k": 5}).json()
    assert search["results"]
    detail = client.get(f"/api/v1/sources/{search['results'][0]['source_id']}")
    assert detail.status_code == 200
    assert detail.json()["body"]
    draft = client.post("/api/v1/posts/draft", json={"intent": "起草失物招领", "image_url": "synthetic-card.png"}).json()
    draft_id = draft["draft"]["draft_id"]
    feedback = client.post(f"/api/v1/posts/draft/{draft_id}/feedback", json={"feedback": "标题改成 图书馆校园卡招领"}).json()
    assert feedback["draft"]["edit_round"] == 1
    blocked_publish = client.post(
        f"/api/v1/posts/draft/{draft_id}/feedback", json={"publish": True}
    )
    assert blocked_publish.status_code == 409
    confirmed = client.post(
        f"/api/v1/posts/draft/{draft_id}/feedback", json={"confirm": True}
    )
    assert confirmed.json()["draft"]["confirmed"] is True
    published = client.post(
        f"/api/v1/posts/draft/{draft_id}/feedback", json={"publish": True}
    )
    assert published.status_code == 200
    assert published.json()["draft"]["published"] is True
    assert client.get(f"/api/v1/posts/{published.json()['post']['post_id']}").status_code == 200
    repeated = client.post(
        f"/api/v1/posts/draft/{draft_id}/feedback", json={"publish": True}
    )
    assert repeated.json()["post"]["post_id"] == published.json()["post"]["post_id"]
    event_draft = client.post(
        "/api/v1/posts/draft",
        json={"intent": "发布学院迎新活动，周五晚七点开始", "category": "活动"},
    )
    assert event_draft.status_code == 200
    assert event_draft.json()["draft"]["category"] == "活动"
    memories = client.get("/api/v1/memories?user_id=demo-user").json()
    assert "memories" in memories
    metrics = client.get("/metrics")
    assert metrics.status_code == 200


def test_platform_management_flows() -> None:
    client = TestClient(app)
    session = client.post(
        "/api/v1/sessions", json={"user_id": "platform-user", "title": "校园咨询"}
    )
    assert session.status_code == 200
    session_id = session.json()["session_id"]
    assert client.get("/api/v1/sessions?user_id=platform-user").json()[0]["session_id"] == session_id

    provider = client.post(
        "/api/v1/providers",
        json={
            "name": "不可达测试模型",
            "role": "chat",
            "tier": "cloud_fallback",
            "base_url": "http://127.0.0.1:9/v1",
            "model": "test-model",
            "api_key": "test-secret-key",
        },
    )
    assert provider.status_code == 201
    assert provider.json()["api_key_present"] is True
    assert "api_key" not in provider.json()
    provider_id = provider.json()["provider_id"]
    checked = client.post(f"/api/v1/providers/{provider_id}/check")
    assert checked.json()["last_check_status"] == "failed"
    assert client.delete(f"/api/v1/providers/{provider_id}").status_code == 200
    assert client.delete(
        f"/api/v1/sessions/{session_id}?user_id=platform-user"
    ).status_code == 200


def test_published_self_fact_is_available_as_long_term_memory() -> None:
    client = TestClient(app)
    user_id = "published-memory-user"
    created = client.post(
        "/api/v1/posts/draft",
        json={
            "intent": "我住在生活区西区，想找同学一起晨跑",
            "category": "生活",
            "user_id": user_id,
            "session_id": "published-memory-session",
        },
    )
    draft_id = created.json()["draft"]["draft_id"]
    assert client.post(
        f"/api/v1/posts/draft/{draft_id}/feedback", json={"confirm": True}
    ).status_code == 200
    published = client.post(
        f"/api/v1/posts/draft/{draft_id}/feedback", json={"publish": True}
    )
    assert published.status_code == 200
    memories = client.get(f"/api/v1/memories?user_id={user_id}").json()["memories"]
    assert any("我住在生活区西区" in item["value"] for item in memories)
