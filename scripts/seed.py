from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.domain.enums import PostCategory
from app.domain.schemas import Post, PostImage
from app.services.repository import JsonRepository, now_iso


DOC_TOPICS = [
    ("doc-library-hours", "图书馆开放时间", "图书馆周一至周日 8:00-22:30 开放，考试周延长到 23:30。闭馆前 15 分钟停止入馆。"),
    ("doc-dorm-repair", "宿舍维修流程", "宿舍报修通过后勤小程序提交；紧急漏水可拨打校内 82200110，维修通常 24 小时内响应。"),
    ("doc-card-loss", "一卡通挂失补办", "一卡通丢失后应先在校园卡中心或自助机挂失，补办地点在学生服务中心一楼。"),
    ("doc-scholarship", "奖学金申请", "奖学金申请需要成绩排名、志愿服务记录和学院公示，材料由辅导员统一收取。"),
    ("doc-clinic", "校医院服务", "校医院工作日 8:30-17:00 开诊；夜间急诊请前往合作医院并保留票据。"),
    (
        "doc-canteen",
        "学生食堂服务",
        "一食堂位于生活区东侧，二食堂位于宿舍区南侧。一食堂工作日供应早餐 6:50-9:00、午餐 10:50-13:30、晚餐 16:40-19:30；二食堂一层设有清真窗口。",
    ),
    ("doc-course-selection", "选课与退课说明", "本学期选课在教务系统进行，补退选开放至开课后第一周周五 17:00，容量变动以系统显示为准。"),
    ("doc-exam", "期末考试安排", "期末考试安排由教务处统一发布；学生须携带校园卡和身份证明，开考 30 分钟后不得进入考场。"),
    ("doc-sports", "体育馆预约规则", "体育馆羽毛球和篮球场通过校园服务平台预约，每人每天最多预约一次，开始前 15 分钟可取消。"),
    ("doc-delivery", "快递服务说明", "南门快递驿站工作日 8:30-21:00 营业，超过 5 天未取件请联系驿站处理。"),
    ("doc-counseling", "心理咨询预约", "心理中心提供保密预约咨询，可在学生服务平台预约；紧急心理危机请联系校医院急诊或当地紧急服务。"),
    ("doc-network", "校园网与宿舍网络", "校园网账号可在信息服务大厅重置密码；宿舍网络故障请提交网络报修单并填写楼栋和房间号。"),
    ("doc-bus", "校车与通勤车", "工作日北门至主校区通勤车 7:20、12:20、17:40 发车，节假日安排以官方通知为准。"),
    ("doc-internship", "实习证明办理", "实习证明需提交单位名称、实习起止时间和学院审核材料，学生服务中心在三个工作日内处理。"),
    ("doc-club", "社团活动申请", "校园活动需至少提前 5 个工作日提交场地和安全申请，涉及校外人员须同步登记。"),
    ("doc-graduation", "毕业手续清单", "毕业生离校前需完成图书归还、宿舍验收、财务结算和档案去向确认，具体时间以学院通知为准。"),
    (
        "doc-timetable",
        "课表与上课时间查询",
        "个人课表可在教务系统首页的“我的课表”查看，也可在校园服务小程序进入教务服务查询。"
        "课程调整、教室变更和停调课信息以教务系统最新通知为准。",
    ),
]

# High-confidence service answers need several independently retrievable notices.
# The remaining documents preserve broad campus-demo coverage.
RETRIEVAL_SUPPORT_TOPICS = [
    DOC_TOPICS[2],
    DOC_TOPICS[2],
    DOC_TOPICS[2],
    DOC_TOPICS[2],
    DOC_TOPICS[2],
    DOC_TOPICS[0],
    DOC_TOPICS[0],
    DOC_TOPICS[0],
    DOC_TOPICS[1],
    DOC_TOPICS[1],
    DOC_TOPICS[4],
    DOC_TOPICS[6],
    DOC_TOPICS[8],
    DOC_TOPICS[9],
    DOC_TOPICS[10],
    DOC_TOPICS[11],
    DOC_TOPICS[12],
    DOC_TOPICS[14],
    DOC_TOPICS[15],
    DOC_TOPICS[3],
    DOC_TOPICS[5],
    DOC_TOPICS[7],
    DOC_TOPICS[13],
]

LOCATIONS = ["图书馆", "南门", "北门", "一食堂", "二食堂", "体育馆", "教学楼A", "学生服务中心"]
OBJECTS = ["黑色雨伞", "蓝色水杯", "白色耳机", "校园卡", "计算器", "钥匙", "帆布包", "教材"]


DEMO_POSTS = [
    ("活动", "本周五体育馆夜跑报名", "体育馆夜跑活动本周五 20:00 集合，已预约的同学请从东门签到。新手也可以报名，现场有配速组。", "体育馆", ["夜跑", "体育馆", "校园活动"]),
    ("校园问答", "请问二食堂清真窗口几点结束？", "想和同学晚课后去二食堂，想确认清真窗口晚餐供应时间。知道的同学麻烦分享一下。", "二食堂", ["食堂", "清真", "校园问答"]),
    ("失物招领", "南门快递驿站捡到一副白色耳机", "下午在南门快递驿站取件区捡到白色蓝牙耳机，盒子上有贴纸。失主请说明耳机型号和贴纸颜色后联系认领。", "南门", ["失物招领", "白色耳机", "快递"]),
    ("二手", "出一台九成新计算器", "课程结束后出一台科学计算器，按键正常、带保护套，可在教学楼 A 当面验机。", "教学楼A", ["二手", "计算器", "当面交易"]),
    ("拼车", "周日去高铁站拼车", "周日下午 15:30 从北门出发去高铁站，还有两个座位，行李不多的同学可以一起分摊车费。", "北门", ["拼车", "高铁站", "周日"]),
    ("学习", "期末周自习搭子招募", "计划每天 9:00-12:00 在图书馆三层复习数据结构，安静学习，结束后互相抽查知识点。", "图书馆", ["学习", "期末", "自习"]),
    ("生活", "宿舍热水维修进度互助帖", "本楼热水不稳定，已经通过后勤小程序报修。大家可以补充楼层和时间，方便统一反馈。", "学生宿舍", ["生活", "宿舍", "报修"]),
    ("校园问答", "校园网密码重置后多久生效？", "昨晚在信息服务大厅重置了校园网密码，宿舍电脑还无法登录。想问通常需要等待多久。", "学生服务中心", ["校园网", "密码", "校园问答"]),
    ("活动", "春季社团市集摊位征集", "本周六在学生活动中心广场举办社团市集，社团可提交摊位申请，欢迎摄影、桌游和公益类社团参与。", "学生活动中心", ["社团", "市集", "活动"]),
    ("失物招领", "图书馆门口发现蓝色校园卡", "在图书馆门口长椅发现一张蓝色校园卡，已交到一楼服务台。失主请携带有效证件前往领取。", "图书馆", ["失物招领", "校园卡", "蓝色"]),
    ("吐槽", "教学楼 A 晚课后空调太冷", "晚课结束时教室空调温度偏低，建议后勤能根据晚间课程时段调整。", "教学楼A", ["吐槽", "空调", "教学楼"]),
    ("二手", "转让两张羽毛球场预约", "周三 19:00 的体育馆羽毛球场临时有事不能去，按预约规则办理转让，有需要的同学私信。", "体育馆", ["二手", "羽毛球", "体育馆"]),
]


def build_documents() -> list[dict[str, str]]:
    docs = []
    topics = DOC_TOPICS + RETRIEVAL_SUPPORT_TOPICS
    for index, (source_id, title, body) in enumerate(topics):
        docs.append(
            {
                "source_id": f"{source_id}-{index:02d}",
                "source_type": "official",
                "title": title if index < len(DOC_TOPICS) else f"{title}（补充说明）",
                "body": f"{body} 本条适用于 2026 春夏学期。",
                "official": "true",
                "path": f"data/campus_docs/{source_id}-{index:02d}.md",
                "url": f"https://campus.example.edu/docs/{source_id}-{index:02d}",
            }
        )
    return docs


def build_posts() -> list[Post]:
    posts = [
        Post(
            post_id=f"post-demo-{index:02d}",
            title=title,
            body=body,
            category=PostCategory(category),
            tags=tags,
            location=location,
            images=[
                PostImage(
                    image_id=f"img-demo-{index:02d}",
                    url=f"/demo_images/{index:02d}.png",
                    alt_text=f"{title}，{location}",
                    attributes={"location_hint": location},
                )
            ]
            if category == PostCategory.LOST_FOUND.value
            else [],
            author_alias=f"校园同学{index + 1:02d}",
            created_at=f"2026-07-{24 - index:02d}T09:00:00+00:00",
        )
        for index, (category, title, body, location, tags) in enumerate(DEMO_POSTS)
    ]
    categories = list(PostCategory)
    for index in range(300 - len(DEMO_POSTS)):
        category = categories[index % len(categories)]
        cycle = index // len(categories)
        location = LOCATIONS[(index + cycle) % len(LOCATIONS)]
        obj = OBJECTS[(index + cycle * 3) % len(OBJECTS)]
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
    print("seeded 300 posts and 40 official documents")


if __name__ == "__main__":
    main()
