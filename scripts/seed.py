from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.domain.enums import PostCategory
from app.domain.schemas import Post, PostImage
from app.services.repository import JsonRepository, now_iso


DOC_TOPICS = [
    ("doc-library-hours", "图书馆开放时间", "图书馆 周一至周日 8:00-22:30 开放，考试周延长到 23:30。闭馆前 15 分钟停止入馆。"),
    ("doc-dorm-repair", "宿舍维修流程", "宿舍报修 通过后勤小程序提交，紧急漏水可拨打校内 82200110。维修通常 24 小时内响应。"),
    ("doc-card-loss", "一卡通挂失补办", "一卡通 丢失后应先在校园卡中心或自助机挂失，补办地点在学生服务中心一楼。"),
    ("doc-scholarship", "奖学金申请", "奖学金申请 需要成绩排名、志愿服务记录和学院公示，材料由辅导员统一收取。"),
    ("doc-clinic", "校医院服务", "校医院 工作日 8:30-17:00 开诊，夜间急诊请前往合作医院并保留票据。"),
]

LOCATIONS = ["图书馆", "南门", "北门", "一食堂", "二食堂", "体育馆", "教学楼A", "学生服务中心"]
OBJECTS = ["黑色雨伞", "蓝色水杯", "白色耳机", "校园卡", "计算器", "钥匙", "帆布包", "教材"]


def build_documents() -> list[dict[str, str]]:
    docs = []
    for index in range(30):
        source_id, title, body = DOC_TOPICS[index % len(DOC_TOPICS)]
        docs.append(
            {
                "source_id": f"{source_id}-{index:02d}",
                "source_type": "official",
                "title": f"{title} {index + 1}",
                "body": f"{body} 本条为第 {index + 1} 条校园官方说明，适用于 2026 春夏学期。",
                "official": "true",
                "path": f"data/campus_docs/{source_id}-{index:02d}.md",
                "url": f"https://campus.example.edu/docs/{source_id}-{index:02d}",
            }
        )
    return docs


def build_posts() -> list[Post]:
    posts = []
    categories = list(PostCategory)
    for index in range(300):
        category = categories[index % len(categories)]
        location = LOCATIONS[index % len(LOCATIONS)]
        obj = OBJECTS[index % len(OBJECTS)]
        title = f"{location}{category.value}信息 {index + 1}"
        if category == PostCategory.LOST_FOUND:
            title = f"{location}附近捡到{obj}"
        body = (
            f"匿名同学分享：今天在{location}遇到和{category.value}相关的事情。"
            f"关键词包括 {obj}、校园服务、开放时间和同学互助。编号 {index + 1}。"
        )
        images = []
        if category == PostCategory.LOST_FOUND:
            images.append(
                PostImage(
                    image_id=f"img-{index:03d}",
                    url=f"/demo_images/lost-{index % 8}.png",
                    alt_text=f"{obj} 在 {location}",
                    attributes={"category": obj, "color": obj[:2], "location_hint": location},
                )
            )
        posts.append(
            Post(
                post_id=f"post-seed-{index:03d}",
                title=title,
                body=body,
                category=category,
                tags=[category.value, location, obj],
                location=location,
                images=images,
                author_alias=f"匿名同学{index % 40:02d}",
                created_at=now_iso(),
            )
        )
    return posts


def main() -> None:
    repo = JsonRepository()
    repo.save_documents(build_documents())
    repo.save_posts(build_posts())
    print("seeded 300 posts and 30 official documents")


if __name__ == "__main__":
    main()

