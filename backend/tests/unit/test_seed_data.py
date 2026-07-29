from scripts.normalize_community_posts import normalize_posts
from scripts.seed import build_documents, build_posts


def test_seed_data_covers_multiple_campus_demo_scenarios() -> None:
    posts = build_posts()
    documents = build_documents()

    assert len(posts) == 300
    assert len(documents) == 43
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
    assert {
        "学生食堂服务",
        "选课与退课说明",
        "体育馆预约规则",
        "校园网与宿舍网络",
        "课表与上课时间查询",
    } <= titles
    assert len([item for item in documents if item["data_mode"] == "verified_official"]) == 3
    assert len([item for item in documents if item["data_mode"] == "demo"]) == 40
    assert all("campus.example.edu" not in item["url"] for item in documents)


def test_imported_community_posts_keep_direct_user_voice() -> None:
    rows = [
        {
            "title": "图书馆还书服务咨询",
            "body": "匿名摘要：有同学询问图书馆是否可以还书。",
            "author_alias": "匿名外部社区",
            "tags": ["哆啦校园", "外部社区快照", "图书馆", "还书"],
        }
    ]

    assert normalize_posts(rows) == 1
    assert rows[0]["author_alias"] == "匿名同学"
    assert rows[0]["body"].startswith("请问学校图书馆")
    assert "匿名摘要" not in rows[0]["body"]
    assert rows[0]["tags"] == ["图书馆", "还书", "社区转帖"]
