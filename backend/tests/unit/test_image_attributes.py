from __future__ import annotations

import pytest

from app.multimodal.image_attributes import enhance_query_with_image, extract_image_attributes


@pytest.mark.asyncio
async def test_image_attributes_feed_query_expansion() -> None:
    attrs = await extract_image_attributes("synthetic-card-library-blue.png")
    query = enhance_query_with_image("帮我找", attrs)
    assert "校园卡" in query
    assert "蓝色" in query

