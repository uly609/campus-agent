from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.enums import PostCategory
from app.domain.schemas import Claim, PostCreate


def test_post_schema_validates_boundaries() -> None:
    post = PostCreate(title="图书馆问题", body="今晚图书馆几点关门？", category=PostCategory.QA)
    assert post.category == PostCategory.QA
    with pytest.raises(ValidationError):
        PostCreate(title="短", body="", category=PostCategory.QA)


def test_claim_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        Claim(claim_id="c1", text="图书馆十点关门", evidence_ids=[])

