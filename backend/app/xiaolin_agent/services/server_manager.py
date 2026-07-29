from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, ClassVar

from app.agent.skills.registry import default_skill_registry
from app.agent.tools.campus_tools import build_registry


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


class ServerManager:
    """XiaoLin's MCP manager interface adapted to the current in-process tool server."""

    _instance: ClassVar[ServerManager | None] = None
    _initialized: ClassVar[bool] = False
    _servers: ClassVar[dict[str, _RegistryServer]] = {}
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _cached_tools: ClassVar[list[Tool]] = []

    @classmethod
    async def get_instance(cls) -> ServerManager:
        if cls._instance is None:
            cls._instance = cls()
        if not cls._initialized:
            async with cls._lock:
                if not cls._initialized:
                    server = _RegistryServer()
                    cls._servers = {server.name: server}
                    cls._cached_tools = await server.list_tools()
                    cls._initialized = True
        return cls._instance

    @classmethod
    def get_cached_tools(cls) -> list[Tool]:
        return list(cls._cached_tools)

    async def list_all_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        for server in self._servers.values():
            tools.extend(await server.list_tools())
        return tools

    async def execute_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        return await self._servers[server_name].execute_tool(tool_name, arguments)
