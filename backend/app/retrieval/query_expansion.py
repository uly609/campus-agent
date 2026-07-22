from __future__ import annotations


DOMAIN_EXPANSIONS = {
    "library": (["图书馆", "闭馆"], "图书馆 开放时间 闭馆 考试周"),
    "card": (["一卡通", "校园卡", "补卡"], "一卡通 校园卡 挂失 补办 学生服务中心"),
    "dorm": (["宿舍", "寝室", "报修", "后勤维修"], "宿舍 后勤 报修 维修 漏水 响应"),
    "scholarship": (["奖学金"], "奖学金 申请 材料 成绩排名 辅导员"),
    "clinic": (["校医院", "急诊", "看诊", "票据"], "校医院 开诊 夜间急诊 合作医院 保留票据"),
}


def expand_campus_query(query: str) -> str:
    additions = [terms for anchors, terms in DOMAIN_EXPANSIONS.values() if any(anchor in query for anchor in anchors)]
    return " ".join([query, *additions])
