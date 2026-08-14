from __future__ import annotations

from enum import StrEnum


class PostCategory(StrEnum):
    QA = "校园问答"
    LOST_FOUND = "失物招领"
    EVENT = "活动"
    SECOND_HAND = "二手"
    CARPOOL = "拼车"
    RANT = "吐槽"
    STUDY = "学习"
    LIFE = "生活"
    KNOWLEDGE_QA = "知识问答"
    RESOURCE = "资源共享"
    COLLABORATION = "业务协作"
    EXPERIENCE = "经验分享"


class MemoryType(StrEnum):
    PREFERENCE = "preference"
    FACT = "fact"
    EVENT = "event"


class Intent(StrEnum):
    GREETING = "greeting"
    CAMPUS_QA = "campus_qa"
    POST_SEARCH = "post_search"
    LOST_FOUND = "lost_found"
    POST_DRAFT = "post_draft"
    MEMORY = "memory"
    EVAL = "eval"
