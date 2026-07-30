# Adapted with author permission from 20czy/zafu_xiaolin_campus_agent at 1b678bd.
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from app.campus_skills.services.weather_service import query_weather


mcp = FastMCP("campusflow-weather")


@mcp.tool()
async def campus_weather(location: str = "杭州", days: int = 1) -> Dict[str, Any]:
    """查询杭州、浙江工商大学下沙校区或教工路校区当前天气和未来 1-7 天天气预报。"""
    return await query_weather(location=location, days=days)


if __name__ == "__main__":
    mcp.run()
