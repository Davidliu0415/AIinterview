from app.services.llm import extract_json_object, fallback_resume_analysis, normalize_score


def test_extract_json_object_from_plain_json():
    assert extract_json_object('{"score": 90}', {"score": 0}) == {"score": 90}


def test_extract_json_object_from_markdown_fence():
    content = '```json\n{"next_action": "ask_next", "next_question": "Q"}\n```'
    assert extract_json_object(content, {})["next_question"] == "Q"


def test_extract_json_object_returns_fallback_when_invalid():
    fallback = {"ok": False}
    assert extract_json_object("not json", fallback) == fallback


def test_fallback_resume_analysis_detects_keywords():
    analysis = fallback_resume_analysis("熟悉 Java、Spring Boot、MySQL、Redis 和 Git。")
    assert "Java" in analysis["skills"]["java"]
    assert "Spring Boot" in analysis["skills"]["spring"]
    assert "MySQL" in analysis["skills"]["database"]


def test_normalize_score_accepts_common_scales():
    assert normalize_score(4) == 80
    assert normalize_score(8) == 80
    assert normalize_score(88.4) == 88
    assert normalize_score(120) == 100
