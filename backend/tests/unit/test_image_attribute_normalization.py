from app.multimodal.image_attributes import normalize_image_attributes


def test_english_vlm_attributes_are_normalized_for_chinese_ui() -> None:
    result = normalize_image_attributes(
        {
            "category": "water bottle",
            "color": "blue",
            "material": "stainless steel",
            "location_hints": ["library", "outdoor seating area", "modern building", "ignored"],
            "confidence": 0.95,
        }
    )

    assert result["category"] == "水杯"
    assert result["color"] == "蓝色"
    assert result["material"] == "不锈钢"
    assert result["location_hints"] == ["图书馆", "室外休息区", "教学楼附近"]


def test_single_location_hint_is_normalized_to_a_list() -> None:
    result = normalize_image_attributes({"category": "水瓶", "location_hints": "图书馆外"})

    assert result["location_hints"] == ["图书馆外"]
