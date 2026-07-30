from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.agent.skills.registry import default_skill_registry
from app.agent.tools.campus_tools import build_registry

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    server_name: str = "campusflow-registry"

    def format_for_llm(self) -> str:
        return f"""
Tool: {self.name}
Description: {self.description}
Arguments: {self.input_schema}
"""


class _RegistryServer:
    name = "campusflow-registry"

    async def list_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        for skill in default_skill_registry().skills:
            for tool_name in skill.tools:
                if tool_name in {"search_official_web", "query_campus_weather"}:
                    continue
                tools.append(
                    Tool(
                        name=tool_name,
                        description=f"{skill.description} Skill: {skill.name}.",
                        input_schema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "params": {"type": "object"},
                            },
                        },
                    )
                )
        return tools

    async def execute_tool(self, tool_name: str, params: dict[str, Any]) -> Any:
        result = await build_registry().call(tool_name, params)
        if not result.success:
            return {"error": result.error_message or result.error_code or "工具执行失败"}
        return result.data


class _WeatherMCPServer:
    name = "campusflow-weather"

    def __init__(self) -> None:
        self.parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "scripts.weather_mcp_server"],
            env=dict(os.environ),
            cwd=Path.cwd(),
        )

    async def list_tools(self) -> list[Tool]:
        async with stdio_client(self.parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
        return [
            Tool(
                name=item.name,
                description=item.description or "通过 FastMCP 查询校园天气。",
                input_schema=item.inputSchema,
                server_name=self.name,
            )
            for item in result.tools
        ]

    async def execute_tool(self, tool_name: str, params: dict[str, Any]) -> Any:
        async with stdio_client(self.parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, params)
        if result.isError:
            return {"error": "FastMCP weather tool returned an error"}
        structured = getattr(result, "structuredContent", None)
        if isinstance(structured, dict):
            payload: Any = structured
        else:
            values: list[Any] = []
            for block in result.content:
                text = getattr(block, "text", None)
                if not isinstance(text, str):
                    continue
                try:
                    values.append(json.loads(text))
                except json.JSONDecodeError:
                    values.append(text)
            payload = values[0] if len(values) == 1 else values
        if isinstance(payload, dict):
            payload["mcp_server"] = self.name
            payload["mcp_transport"] = "stdio"
            payload["data_mode"] = "live_external"
        return payload


class ServerManager:
    """XiaoLin's MCP manager interface adapted to the current in-process tool server."""

    _instance: ClassVar[ServerManager | None] = None
    _initialized: ClassVar[bool] = False
    _servers: ClassVar[dict[str, Any]] = {}
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _cached_tools: ClassVar[list[Tool]] = []

    @classmethod
    async def get_instance(cls) -> ServerManager:
        if cls._instance is None:
            cls._instance = cls()
        if not cls._initialized:
            async with cls._lock:
                if not cls._initialized:
                    registry_server = _RegistryServer()
                    weather_server = _WeatherMCPServer()
                    cls._servers = {
                        registry_server.name: registry_server,
                        weather_server.name: weather_server,
                    }
                    cls._cached_tools = await registry_server.list_tools()
                    try:
                        cls._cached_tools.extend(await weather_server.list_tools())
                    except Exception:
                        logger.error("FastMCP weather discovery failed", exc_info=True)
                    cls._initialized = True
        return cls._instance

    @classmethod
    def get_cached_tools(cls) -> list[Tool]:
        return list(cls._cached_tools)

    async def list_all_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        for server in self._servers.values():
            try:
                tools.extend(await server.list_tools())
            except Exception:
                logger.error("MCP tool discovery failed for %s", server.name, exc_info=True)
        return tools

    async def execute_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        return await self._servers[server_name].execute_tool(tool_name, arguments)
