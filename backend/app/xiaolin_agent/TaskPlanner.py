from __future__ import annotations

import json
import logging
from typing import Any

from app.xiaolin_agent.services.llm_service import LLMService, MAIN_AGENT_MODEL
from app.xiaolin_agent.services.student_profile_service import format_student_profile_for_prompt

logger = logging.getLogger(__name__)


class TaskPlanner:
    """Central planning LLM that decomposes user requests into subtasks."""

    PLANNING_PROMPT = """你是浙江工商大学智能校园系统的中央规划器。你的任务是在校园场景下，分析用户的请求，并将其分解为可处理的子任务。

分析用户请求，并以下格式返回任务计划：

{{
  "tasks": [
    {{
      "id": 1,
      "task": "具体任务描述",
      "input": "给该任务的输入",
      "depends_on": []
    }},
    {{
      "id": 2,
      "task": "具体任务描述",
      "input": "给该任务的输入",
      "depends_on": [1]
    }}
  ]
}}

规则：
1. 每个任务应尽可能精确
2. 如果任务之间有依赖关系，请使用depends_on字段指定
3. 复杂请求应分解为多个子任务
4. 简单请求可以是单个任务

当前用户画像：
{student_profile}

用户请求："{user_request}"
"""

    @classmethod
    async def create_task_plan(cls, user_request: str) -> dict[str, Any]:
        logger.info("开始创建任务计划")
        try:
            prompt = cls.PLANNING_PROMPT.format(
                user_request=user_request,
                student_profile=format_student_profile_for_prompt(),
            )
            llm = await LLMService.get_llm(model_name=MAIN_AGENT_MODEL, temperature=0.2)
            planning_response = await llm.ainvoke(
                [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_request},
                ]
            )
            response_text = str(planning_response.content)
            json_match = response_text.strip()
            if "```json" in json_match:
                json_match = json_match.split("```json", 1)[1].split("```", 1)[0]
            task_plan = json.loads(json_match)
            if not isinstance(task_plan, dict):
                raise TypeError("任务计划必须是 JSON 对象")
            return task_plan
        except json.JSONDecodeError:
            logger.error("任务规划 JSON 解析错误", exc_info=True)
            return await cls._get_fallback_plan(user_request)
        except Exception:
            logger.error("任务规划过程出错", exc_info=True)
            return await cls._get_fallback_plan(user_request)

    @classmethod
    async def _get_fallback_plan(cls, user_request: str) -> dict[str, Any]:
        logger.warning("使用小林原版降级任务计划")
        return {
            "tasks": [
                {
                    "id": 1,
                    "task": "处理用户请求",
                    "input": user_request,
                    "depends_on": [],
                }
            ],
            "final_output_task_id": 1,
        }
