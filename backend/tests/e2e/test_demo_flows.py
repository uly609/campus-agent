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

