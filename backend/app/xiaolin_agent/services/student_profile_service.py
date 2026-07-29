from __future__ import annotations

from app.campus_skills.services.student_profile_service import parse_student_profile


def format_student_profile_for_prompt() -> str:
    profile = parse_student_profile()
    allowed_fields = ("学院", "专业", "年级", "校区")
    visible = {
        key: profile[key]
        for key in allowed_fields
        if key in profile and "未配置" not in profile[key]
    }
    if not visible:
        return "当前没有可用于聊天的学生画像信息。"
    lines = "\n".join(f"- {key}: {value}" for key, value in visible.items())
    return f"""当前用户的非身份化校园上下文：
{lines}

使用要求：
1. 仅在问题相关时使用这些上下文。
2. 不要猜测或称呼用户姓名，也不要输出学号、班级、宿舍、联系方式等个人信息。
3. 用户没有明确提供的信息一律视为未知。"""


__all__ = ["format_student_profile_for_prompt"]
