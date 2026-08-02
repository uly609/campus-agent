from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.enums import PostCategory
from app.domain.schemas import ChatFileUpload, ChatRequest, Claim, PostCommentCreate, PostCreate


def test_post_schema_validates_boundaries() -> None:
    post = PostCreate(title="图书馆问题", body="今晚图书馆几点关门？", category=PostCategory.QA)
    assert post.category == PostCategory.QA
    with pytest.raises(ValidationError):
        PostCreate(title="短", body="", category=PostCategory.QA)


def test_comment_schema_trims_and_rejects_blank_content() -> None:
    assert PostCommentCreate(body="  想了解具体时间  ").body == "想了解具体时间"
    with pytest.raises(ValidationError):
        PostCommentCreate(body="   ")


def test_claim_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        Claim(claim_id="c1", text="图书馆十点关门", evidence_ids=[])


def test_chat_images_require_safe_supported_urls() -> None:
    request = ChatRequest(
        message="看看图片",
        image_urls=["data:image/png;base64,dGVzdA=="],
    )
    assert len(request.image_urls) == 1

    with pytest.raises(ValidationError):
        ChatRequest(message="看看图片", image_urls=["http://private.example/image.png"])


def test_chat_file_accepts_supported_base64_document() -> None:
    request = ChatRequest(
        message="分析课表",
        files=[
            ChatFileUpload(
                name="课表.xlsx",
                data_url="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,AA==",
            )
        ],
        is_agent=True,
    )

    assert request.files[0].name == "课表.xlsx"


def test_chat_file_rejects_unsupported_document() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(
            message="运行附件",
            files=[ChatFileUpload(name="脚本.exe", data_url="data:application/octet-stream;base64,AA==")],
        )
