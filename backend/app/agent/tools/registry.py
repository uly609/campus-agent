from __future__ import annotations

import time
from typing import Awaitable, Callable

from app.domain.schemas import ToolResult
from app.observability.metrics import TOOL_CALLS, TOOL_FAILURES, TOOL_LATENCY
from app.security.tool_permissions import assert_tool_allowed

ToolCallable = Callable[[dict[str, object]], Awaitable[ToolResult]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolCallable] = {}

    def register(self, name: str, tool: ToolCallable) -> None:
        assert_tool_allowed(name)
        self._tools[name] = tool

    async def call(self, name: str, payload: dict[str, object]) -> ToolResult:
        assert_tool_allowed(name)
        if name not in self._tools:
            return ToolResult(
                tool_name=name,
                success=False,
                data=None,
                error_code="TOOL_NOT_REGISTERED",
                error_message=f"{name} is not registered",
                latency_ms=0,
                provenance=[],
            )
        start = time.perf_counter()
        result = await self._tools[name](payload)
        latency_ms = int((time.perf_counter() - start) * 1000)
        result.latency_ms = latency_ms
        TOOL_CALLS.labels(tool=name, status="ok" if result.success else "failed").inc()
        TOOL_LATENCY.labels(tool=name).observe(latency_ms / 1000)
        if not result.success:
            TOOL_FAILURES.labels(tool=name).inc()
        return result

