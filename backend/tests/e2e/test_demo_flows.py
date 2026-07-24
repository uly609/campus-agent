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
    draft = client.post("/api/v1/posts/draft", json={"intent": "起草失物招领", "image_url": "synthetic-card.png"}).json()
    draft_id = draft["draft"]["draft_id"]
    feedback = client.post(f"/api/v1/posts/draft/{draft_id}/feedback", json={"feedback": "标题改成 图书馆校园卡招领"}).json()
    assert feedback["draft"]["edit_round"] == 1
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
