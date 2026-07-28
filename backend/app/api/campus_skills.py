from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.campus_skills.adapters import (
    course_evidence,
    notice_evidence,
    profile_evidence,
    reservation_draft,
    venue_evidence,
    weather_evidence,
)

router = APIRouter(prefix="/api/v1/campus", tags=["campus-skills"])


class VenueDraftRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


@router.get("/capabilities")
def capabilities() -> dict[str, object]:
    return {
        "degraded_mode": False,
        "data_mode": "synthetic-demo",
        "skills": [
            {"name": "course_schedule", "tool": "query_course_schedule", "live": True},
            {"name": "campus_notice", "tool": "query_campus_notices", "live": True},
            {"name": "venue_coordination", "tool": "query_campus_venues", "live": True},
            {"name": "campus_weather", "tool": "query_campus_weather", "live": True},
            {"name": "student_profile", "tool": "get_student_profile", "live": True},
        ],
        "safety": {
            "profile_fields": "safe-only",
            "reservation_requires_confirmation": True,
            "automatic_booking": False,
            "weather_mcp": {
                "transport": "stdio",
                "command": "python -m scripts.weather_mcp_server",
            },
        },
    }


@router.get("/courses")
def courses(query: str = Query(default="我的课表", max_length=500)) -> list[dict[str, object]]:
    return [item.model_dump() for item in course_evidence({"query": query})]


@router.get("/notices")
def notices(query: str = Query(default="最新通知", max_length=500)) -> list[dict[str, object]]:
    return [item.model_dump() for item in notice_evidence({"query": query})]


@router.get("/venues")
def venues(query: str = Query(default="查询活动场地", max_length=500)) -> list[dict[str, object]]:
    return [item.model_dump() for item in venue_evidence({"query": query})]


@router.get("/weather")
async def weather(query: str = Query(default="杭州今天天气", max_length=500)) -> dict[str, object]:
    evidence, error = await weather_evidence({"query": query})
    return {"available": error is None, "error": error, "evidence": [item.model_dump() for item in evidence]}


@router.get("/profile")
def profile() -> list[dict[str, object]]:
    return [item.model_dump() for item in profile_evidence()]


@router.post("/venue-reservation-draft")
def venue_reservation(payload: VenueDraftRequest) -> dict[str, object]:
    return reservation_draft({"query": payload.query})
