from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import Intent


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str = Field(min_length=1)
    arguments: dict[str, object] = Field(default_factory=dict)

    def to_step(self) -> dict[str, object]:
        return {"tool": self.tool_name, "args": dict(self.arguments)}


class IntentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: Intent
    tool_calls: list[ToolCall] = Field(default_factory=list, max_length=4)
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["model", "fallback"] = "model"

    @model_validator(mode="after")
    def validate_tool_requirement(self) -> IntentPlan:
        if self.intent == Intent.GREETING and self.tool_calls:
            raise ValueError("greeting plans must not call tools")
        if self.intent != Intent.GREETING and not self.tool_calls:
            raise ValueError("non-greeting plans require at least one tool call")
        return self

    def to_steps(self) -> list[dict[str, object]]:
        return [call.to_step() for call in self.tool_calls]
