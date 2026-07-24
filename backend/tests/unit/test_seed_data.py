from scripts.seed import build_documents, build_posts


def test_seed_data_covers_multiple_campus_demo_scenarios() -> None:
    posts = build_posts()
    documents = build_documents()

    assert len(posts) == 300
    assert len(documents) == 40
    assert {post.category.value for post in posts[:12]} == {
        "校园问答",
        "失物招领",
        "活动",
        "二手",
        "拼车",
        "吐槽",
        "学习",
        "生活",
    }
    titles = {document["title"] for document in documents}
    assert {"学生食堂服务", "选课与退课说明", "体育馆预约规则", "校园网与宿舍网络"} <= titles
