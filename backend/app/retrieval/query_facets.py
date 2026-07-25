from __future__ import annotations

import re


LOCATION_QUERY_MARKERS = ("在哪", "哪里", "位置", "地点", "怎么走", "怎么去", "哪一层", "哪个门")
LOCATION_EVIDENCE_MARKERS = (
    "位于",
    "地点",
    "地址",
    "一楼",
    "二楼",
    "三楼",
    "东侧",
    "西侧",
    "南侧",
    "北侧",
    "东门",
    "西门",
    "南门",
    "北门",
    "服务中心",
    "生活区",
    "宿舍区",
)
TIME_QUERY_MARKERS = ("几点", "什么时候", "开放时间", "营业时间", "关门", "闭馆", "截止时间")
TIME_EVIDENCE_MARKERS = ("开放", "营业", "闭馆", "发车", "截止", "工作日", "周一", "周二", "周三", "周四", "周五")
LOOKUP_QUERY_MARKERS = ("哪里看", "在哪看", "怎么查", "如何查", "哪里查询", "在哪查询")


def query_facet(query: str) -> str | None:
    if any(marker in query for marker in LOOKUP_QUERY_MARKERS):
        return None
    if any(marker in query for marker in LOCATION_QUERY_MARKERS):
        return "location"
    if any(marker in query for marker in TIME_QUERY_MARKERS):
        return "time"
    return None


def text_matches_query_facet(query: str, text: str) -> bool:
    facet = query_facet(query)
    if facet is None:
        return True
    if facet == "location":
        return any(marker in text for marker in LOCATION_EVIDENCE_MARKERS)
    return bool(re.search(r"\b\d{1,2}[:：]\d{2}\b", text)) or any(
        marker in text for marker in TIME_EVIDENCE_MARKERS
    )
