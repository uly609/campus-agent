from __future__ import annotations

import re
from typing import Any

from app.campus_skills.services.campus_notice_service import query_mock_campus_notices
from app.campus_skills.services.course_schedule_service import query_mock_course_schedule
from app.campus_skills.services.student_profile_service import parse_student_profile
from app.campus_skills.services.venue_service import handle_venue_request
from app.campus_skills.services.weather_service import query_weather
from app.domain.schemas import Evidence


def _query(payload: dict[str, object]) -> str:
    return str(payload.get("query", "")).strip()


def _course_params(payload: dict[str, object]) -> dict[str, Any]:
    query = _query(payload)
    params: dict[str, Any] = dict(payload)
    params.pop("query", None)
    profile = parse_student_profile()
    scoped = ("major", "grade", "class_name", "course_id", "course_name", "teacher")
    if not any(params.get(key) for key in scoped):
        params.setdefault("major", profile.get("专业"))
        params.setdefault("grade", profile.get("年级", "").replace("级", ""))
        params.setdefault("class_name", profile.get("班级"))
    days = ("今天", "明天", "周一", "周二", "周三", "周四", "周五", "周六", "周日")
    day = next((value for value in days if value in query), None)
    if day:
        params.setdefault("day_of_week", day)
    course_id = re.search(r"\b[A-Za-z]{2,4}\d{3}\b", query)
    if course_id:
        params.setdefault("course_id", course_id.group(0).upper())
    for name in ("数据结构", "计算机导论", "操作系统", "高等数学", "大学英语", "体育"):
        if name in query:
            params.setdefault("course_name", name)
    for campus in ("东湖校区", "衣锦校区"):
        if campus in query:
            params.setdefault("campus", campus)
    return params


def course_evidence(payload: dict[str, object]) -> list[Evidence]:
    result = query_mock_course_schedule(_course_params(payload))
    evidence: list[Evidence] = []
    for index, course in enumerate(result.get("courses", [])[:8], start=1):
        excerpt = (
            f"{course['course_name']}（{course['course_id']}）由{course['instructor']}授课，"
            f"{course['day_label']} {course['time']}，地点为{course['campus']}"
            f"{course['building']} {course['classroom']}。"
        )
        evidence.append(Evidence(
            evidence_id=f"skill-course-{index}-{course['course_id']}",
            source_id=f"xiaolin-course-{course['course_id']}",
            source_type="skill", title=f"课表：{course['course_name']}",
            excerpt=excerpt, score=0.94, official=True,
            metadata={"skill": "course-schedule", "synthetic_demo": True, "raw": course},
        ))
    return evidence


def notice_evidence(payload: dict[str, object]) -> list[Evidence]:
    params: dict[str, Any] = dict(payload)
    params.setdefault("query", _query(payload))
    result = query_mock_campus_notices(params)
    evidence: list[Evidence] = []
    for index, notice in enumerate(result.get("notices", [])[:8], start=1):
        notice_id = str(notice.get("notice_id") or notice["id"])
        content = str(notice.get("summary") or notice.get("content") or "")
        excerpt = (
            f"{notice['title']}。发布部门：{notice['department']}，"
            f"发布日期：{notice['publish_date']}。{content}"
        )
        evidence.append(Evidence(
            evidence_id=f"skill-notice-{index}-{notice_id}",
            source_id=f"xiaolin-notice-{notice_id}",
            source_type="skill", title=notice["title"], excerpt=excerpt[:500],
            score=0.92, official=True,
            metadata={"skill": "campus-notice", "synthetic_demo": True, "raw": notice},
        ))
    return evidence


def _venue_params(payload: dict[str, object]) -> dict[str, Any]:
    query = _query(payload)
    params: dict[str, Any] = dict(payload)
    params.pop("query", None)
    capacity = re.search(r"(\d{2,4})\s*人", query)
    if capacity:
        params.setdefault("attendee_count", int(capacity.group(1)))
    for campus in ("东湖校区", "衣锦校区"):
        if campus in query:
            params.setdefault("campus", campus)
    for event_type in ("讲座", "会议", "培训", "沙龙", "活动", "考试"):
        if event_type in query:
            params.setdefault("event_type", event_type)
    equipment = [item for item in ("投影", "音响", "无线麦克风", "舞台灯光") if item in query]
    if equipment:
        params.setdefault("equipment", equipment)
    date_match = re.search(r"20\d{2}-\d{2}-\d{2}", query)
    if date_match:
        params.setdefault("date", date_match.group(0))
    period_match = re.search(
        r"([01]?\d|2[0-3]):[0-5]\d\s*[-至到]\s*([01]?\d|2[0-3]):[0-5]\d", query
    )
    if period_match:
        period = period_match.group(0).replace("至", "-").replace("到", "-").replace(" ", "")
        params.setdefault("period", period)
    elif "下午" in query:
        params.setdefault("period", "14:00-17:00")
    return params


def venue_evidence(payload: dict[str, object]) -> list[Evidence]:
    params = _venue_params(payload)
    params["action"] = "query"
    result = handle_venue_request(params)
    evidence: list[Evidence] = []
    for index, venue in enumerate(result.get("venues", [])[:8], start=1):
        if not params.get("date") or not params.get("period"):
            availability = "可查询具体日期和时段的预约冲突"
        else:
            availability = "目标时段可用" if venue["available"] else "目标时段存在冲突"
        excerpt = (
            f"{venue['name']}位于{venue['campus']}{venue['building']}{venue['floor']}，"
            f"容量{venue['capacity']}人，设备包括{'、'.join(venue['equipment'])}；{availability}。"
        )
        evidence.append(Evidence(
            evidence_id=f"skill-venue-{index}-{venue['venue_id']}",
            source_id=f"xiaolin-venue-{venue['venue_id']}",
            source_type="skill", title=venue["name"], excerpt=excerpt,
            score=0.9 if venue["available"] else 0.55, official=True,
            metadata={"skill": "venue-booking", "synthetic_demo": True, "raw": venue},
        ))
    return evidence


def reservation_draft(payload: dict[str, object]) -> dict[str, Any]:
    params = _venue_params(payload)
    if not params.get("venue_id"):
        query_params = {**params, "action": "query"}
        candidates = handle_venue_request(query_params).get("venues", [])
        if candidates:
            params["venue_id"] = candidates[0]["venue_id"]
    params["action"] = "reserve"
    result = handle_venue_request(params)
    if result.get("status") == "error" and result.get("missing_fields"):
        result["status"] = "needs_input"
    result.update(requires_confirmation=True, published=False, synthetic_demo=True)
    return result


async def weather_evidence(payload: dict[str, object]) -> tuple[list[Evidence], str | None]:
    query = _query(payload)
    locations = ("东湖校区", "衣锦校区", "临安", "杭州")
    location = next((item for item in locations if item in query), "杭州")
    days_match = re.search(r"(\d)\s*天", query)
    days = int(days_match.group(1)) if days_match else int(str(payload.get("days", 1)))
    result = await query_weather(str(payload.get("location") or location), days)
    if result.get("status") != "success":
        return [], str(result.get("message", "天气服务不可用"))
    current = result["current"]
    forecast = result.get("forecast", [])
    forecast_text = "；".join(
        f"{item['date']} {item['weather']} {item['temperature_min']}-{item['temperature_max']}℃"
        for item in forecast[:days]
    )
    excerpt = (
        f"{result['location']['name']}当前{current['weather']}，气温{current['temperature']}℃，"
        f"湿度{current['humidity']}%，风速{current['wind_speed']}km/h。{forecast_text}"
    )
    return [Evidence(
        evidence_id="skill-weather-open-meteo",
        source_id="open-meteo-campus-weather", source_type="external",
        title=f"{result['location']['name']}天气", excerpt=excerpt,
        score=0.95, official=False,
        metadata={"skill": "campus-weather", "source": "Open-Meteo", "raw": result},
    )], None


def profile_evidence() -> list[Evidence]:
    profile = parse_student_profile()
    safe_fields = ("学院", "专业", "年级", "班级", "导师", "校区")
    excerpt = "；".join(f"{key}：{profile[key]}" for key in safe_fields if profile.get(key))
    return [Evidence(
        evidence_id="skill-profile-demo-user",
        source_id="xiaolin-synthetic-student-profile",
        source_type="profile", title="演示学生画像", excerpt=excerpt,
        score=0.93, official=False,
        metadata={"skill": "student-profile", "synthetic_demo": True},
    )]
