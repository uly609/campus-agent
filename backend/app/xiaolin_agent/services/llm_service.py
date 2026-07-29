from __future__ import annotations

import os
from typing import Any, ClassVar

from dotenv import load_dotenv
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv()

DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
MAIN_AGENT_MODEL = os.getenv("AGENT_MAIN_MODEL", "deepseek-v4-flash")
TOOL_LIBRARY_MODEL = os.getenv("TOOL_LIBRARY_MODEL", "deepseek-v4-flash")


def _resolve_model_name(model_name: str) -> str:
    aliases = {
        "main_agent": MAIN_AGENT_MODEL,
        "tool_library": TOOL_LIBRARY_MODEL,
    }
    return aliases.get(model_name, model_name)


class LLMService:
    """XiaoLin's original cached ChatOpenAI model factory."""

    _llm_instances: ClassVar[dict[str, ChatOpenAI]] = {}

    @classmethod
    async def get_llm(
        cls,
        model_name: str = MAIN_AGENT_MODEL,
        stream: bool = False,
        temperature: float = 0.7,
    ) -> ChatOpenAI:
        model_name = _resolve_model_name(model_name)
        cache_key = f"{model_name}_{stream}_{temperature}"
        if cache_key not in cls._llm_instances:
            cls._llm_instances[cache_key] = cls._create_llm(model_name, stream, temperature)
        return cls._llm_instances[cache_key]

    @staticmethod
    def _create_llm(
        model_name: str = MAIN_AGENT_MODEL,
        stream: bool = False,
        temperature: float = 0.7,
    ) -> ChatOpenAI:
        load_dotenv()
        model_name = _resolve_model_name(model_name)

        if model_name.startswith("deepseek-"):
            api_key = os.getenv("DEEPSEEK_API_KEY")
            url = DEEPSEEK_API_BASE
        elif model_name == "chatglm":
            model_name = "glm-4-flash"
            url = "https://open.bigmodel.cn/api/paas/v4/"
            api_key = os.getenv("GLM_API_KEY")
        else:
            raise ValueError(f"Unsupported model: {model_name}")

        if not api_key:
            raise ValueError(f"API key for {model_name} not found in environment variables")

        callbacks: list[Any] | None = [StreamingStdOutCallbackHandler()] if stream else None
        return ChatOpenAI(
            model=model_name,
            api_key=SecretStr(api_key),
            base_url=url,
            temperature=temperature,
            streaming=stream,
            callbacks=callbacks,
        )


def create_llm(model_name: str = MAIN_AGENT_MODEL, stream: bool = False) -> ChatOpenAI:
    model_name = _resolve_model_name(model_name)
    return LLMService._create_llm(model_name=model_name, stream=stream)
