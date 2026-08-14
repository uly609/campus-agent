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

VERIFIED_OFFICIAL_DOCS = [
    {
        "source_id": "zjsu-library-overview-2022",
        "source_type": "official",
        "title": "浙江工商大学图书馆本馆介绍",
        "body": (
            "浙江工商大学图书馆由下沙校区图书馆和教工路校区图书馆组成。"
            "下沙校区图书馆地址为浙江省杭州市下沙高教园区学正街18号，"
            "图书馆提供书刊外借、阅览、参考咨询、文献检索、馆际互借和文献传递等服务。"
            "该页面标注更新时间为2022年3月，具体开放安排应以图书馆最新通知为准。"
        ),
        "official": "true",
        "path": "official://lib.zjsu.edu.cn/gybg/list.htm",
        "url": "https://lib.zjsu.edu.cn/gybg/list.htm",
        "data_mode": "verified_official",
        "verified_at": "2026-07-29",
    },
    {
        "source_id": "zjsu-library-card-rules",
        "source_type": "official",
        "title": "浙江工商大学图书借阅规则中的校园卡规定",
        "body": (
            "浙江工商大学图书借阅规则规定，读者凭本人校园卡办理图书借阅。"
            "校园卡遗失后，可凭有效证件到校园卡服务部或图书馆挂失。"
            "这是借阅规则，不代表当前校园卡补办地点或办理时间；相关事项应以学校最新服务通知为准。"
        ),
        "official": "true",
        "path": "official://ck.zjsu.edu.cn/library-card-rules.pdf",
        "url": "https://ck.zjsu.edu.cn/_upload/article/files/d6/77/df8c2e8246239ba853c346726497/b50f2b32-0cfb-4d91-ae2b-cca5ee2cef30.pdf",
        "data_mode": "verified_official",
        "verified_at": "2026-07-29",
    },
    {
        "source_id": "zjsu-logistics-services-2026",
        "source_type": "official",
        "title": "浙江工商大学后勤服务中心服务信息",
        "body": (
            "浙江工商大学后勤服务中心网站提供餐饮、公寓、校园卡、物业、商贸和校车等服务入口。"
            "页面列出的24小时服务热线为0571-28008899（下沙）和0571-89808899（教工路），"
            "维修报修热线为0571-28877866。电话和服务安排可能调整，使用前应核对官网最新页面。"
        ),
        "official": "true",
        "path": "official://hq.zjsu.edu.cn/main.htm",
        "url": "https://hq.zjsu.edu.cn/main.htm",
        "data_mode": "verified_official",
        "verified_at": "2026-07-29",
    },
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


ENTERPRISE_DOCS = [
    ("atlas-expense-policy", "差旅与费用报销制度", "员工差旅申请、费用标准、票据要求和审批节点统一在费用平台提交。超过标准的支出需要补充业务负责人和财务负责人的审批意见。"),
    ("atlas-open-api-auth", "开放平台 API 鉴权规范", "开放平台 API 使用 OAuth2 Client Credentials 获取访问令牌。调用方必须按应用分配 scope，服务端校验 token、租户和接口权限，禁止把密钥写入前端或日志。"),
    ("atlas-incident-runbook", "订单服务故障排查手册", "发现错误率、延迟或消息堆积异常时，先确认告警时间窗和影响范围，再检查网关、订单服务、数据库连接池和消息消费组。涉及数据修复必须创建工单并经人工确认。"),
    ("atlas-support-sla", "客户支持 SLA", "P1 级故障需要 15 分钟内响应并持续更新进度，P2 级问题 2 小时内响应，普通咨询在一个工作日内回复。每次升级必须关联客户、服务和事件编号。"),
    ("atlas-data-access", "企业知识库权限与数据分级", "公开资料、部门资料、客户资料和敏感资料按四级管理。检索结果继承文档 ACL，敏感内容默认脱敏；导出和跨部门共享需要审批并记录审计事件。"),
    ("atlas-release-policy", "产品版本发布规范", "版本发布需要完成变更说明、回滚方案、灰度范围和责任人确认。发布后观察核心指标，出现回归时按回滚条件恢复上一稳定版本，并在复盘中补充知识库条目。"),
    ("atlas-contract-review", "合同审批流程", "合同先由业务负责人提交，再经过法务、财务和授权负责人审核。模板外条款必须标明风险点和替代方案，审批完成前不得对外承诺或执行交付。"),
    ("atlas-onboarding", "新员工入职手册", "新员工入职后完成账号申请、权限最小化配置、信息安全培训和团队知识库导览。业务系统权限按岗位申请，离职或转岗时由负责人发起回收。"),
    ("atlas-kb-governance", "知识库入库与审核规范", "文档入库必须记录来源、版本、责任部门和复核时间。解析后先预览切块，再执行索引；失效文档进入 STALE 状态，不能作为高置信度答案的唯一依据。"),
]


ENTERPRISE_POSTS = [
    ("经验分享", "如何定位线上消息积压？", "先确认消费组延迟和积压时间窗，再查看生产速率、消费异常和下游依赖。涉及重放或补偿时必须保留工单号并人工确认。", "SRE", ["消息队列", "故障排查", "经验"]),
    ("知识问答", "开放平台接口应该如何申请权限？", "请先确认应用所属租户和业务场景，再按最小权限申请 scope。生产密钥不能提交到代码仓库，也不能在工单中明文传播。", "开发者平台", ["API", "权限", "安全"]),
    ("经验分享", "一次发布回滚复盘记录", "这次问题来自配置变更没有进入灰度观察。后续发布会把回滚阈值、观察指标和负责人写进发布单，并同步到知识库。", "发布管理", ["发布", "回滚", "复盘"]),
    ("知识问答", "客户投诉升级时需要记录哪些信息？", "至少记录客户、服务、事件编号、影响范围、首次响应时间和当前负责人。信息不完整时先补齐事实，不要直接推断责任。", "客户支持", ["SLA", "工单", "客户支持"]),
    ("资源共享", "整理了一份数据库慢查询排查清单", "包含执行计划、索引命中、锁等待、连接池和最近发布变更几个检查项，欢迎补充真实案例。", "工程效率", ["MySQL", "排障", "清单"]),
    ("业务协作", "本周知识库治理共审了 18 篇文档", "已完成来源、责任人和复核时间补充，其中 3 篇旧版本标记为 STALE，后续会由业务负责人确认是否替换。", "知识治理", ["知识库", "审核", "版本"]),
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
                "body": f"演示资料，非浙江工商大学官方发布：{body} 本条仅用于功能演示。",
                "official": "true",
                "path": f"demo://campus_docs/{source_id}-{index:02d}.md",
                "url": "",
                "data_mode": "demo",
                "verified_at": "",
            }
        )
    return docs + VERIFIED_OFFICIAL_DOCS


def build_enterprise_documents() -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    for source_id, title, body in ENTERPRISE_DOCS:
        docs.append(
            {
                "source_id": source_id,
                "source_type": "official",
                "title": title,
                "body": body,
                "official": "true",
                "path": f"demo://enterprise_docs/{source_id}.md",
                "url": "",
                "data_mode": "enterprise_demo",
                "domain": "enterprise",
                "version": "v1.0",
                "department": "平台运营中心",
                "verified_at": "2026-08-14",
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
            domain="legacy_campus",
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
                domain="legacy_campus",
            )
        )
    return posts


def build_enterprise_posts() -> list[Post]:
    return [
        Post(
            post_id=f"atlas-post-{index:02d}",
            title=title,
            body=body,
            category=PostCategory(category),
            tags=tags,
            location=location,
            author_alias=f"社区成员{index + 1:02d}",
            created_at=now_iso(),
            domain="enterprise",
        )
        for index, (category, title, body, location, tags) in enumerate(ENTERPRISE_POSTS)
    ]


def main() -> None:
    repo = JsonRepository()
    documents = build_documents() + build_enterprise_documents()
    posts = build_posts() + build_enterprise_posts()
    repo.save_documents(documents)
    repo.save_posts(posts)
    print(f"seeded {len(posts)} demo posts and {len(documents)} knowledge documents")


if __name__ == "__main__":
    main()
