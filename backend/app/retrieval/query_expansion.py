from __future__ import annotations


DOMAIN_EXPANSIONS = {
    "library": (["图书馆", "闭馆"], "图书馆 开放时间 闭馆 考试周"),
    "card": (["一卡通", "校园卡", "补卡"], "一卡通 校园卡 挂失 补办 学生服务中心"),
    "dorm": (["宿舍", "寝室", "报修", "后勤维修"], "宿舍 后勤 报修 维修 漏水 响应"),
    "scholarship": (["奖学金"], "奖学金 申请 材料 成绩排名 辅导员"),
    "clinic": (["校医院", "急诊", "看诊", "票据"], "校医院 开诊 夜间急诊 合作医院 保留票据"),
    "canteen": (
        ["食堂", "饭堂", "餐厅", "清真窗口"],
        "一食堂 二食堂 位置 生活区 宿舍区 营业时间 清真窗口",
    ),
    "course": (["选课", "退课", "补退选"], "教务系统 选课 退课 补退选 截止时间"),
    "timetable": (["课表", "课程表", "上课教室"], "个人课表 教务系统 我的课表 上课时间 教室变更"),
    "sports": (["体育馆", "羽毛球场", "篮球场"], "体育馆 场地 位置 预约 取消"),
    "network": (["校园网", "网络故障", "网络报修"], "校园网 信息服务大厅 密码重置 宿舍网络 报修"),
    "delivery": (["快递", "驿站"], "南门 快递驿站 位置 营业时间 取件"),
    "shuttle": (["校车", "通勤车"], "北门 校车 通勤车 发车时间"),
}


def expand_campus_query(query: str) -> str:
    additions = [terms for anchors, terms in DOMAIN_EXPANSIONS.values() if any(anchor in query for anchor in anchors)]
    return " ".join([query, *additions])
