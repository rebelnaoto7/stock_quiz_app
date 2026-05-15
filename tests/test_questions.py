import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "questions.json"


def load_questions():
    with QUESTIONS.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_questions_json_exists_and_is_list():
    assert QUESTIONS.exists()
    questions = load_questions()
    assert isinstance(questions, list)
    assert len(questions) >= 20


def test_required_fields_exist():
    required = {"id", "category", "difficulty", "title", "question", "options", "answer", "point", "explanation"}
    for q in load_questions():
        assert required.issubset(q.keys())


def test_answer_exists_in_options():
    for q in load_questions():
        assert q["answer"] in q["options"]


def test_difficulty_values_are_valid():
    valid = {"初級", "中級", "上級"}
    for q in load_questions():
        assert q["difficulty"] in valid


def test_image_files_exist_when_specified():
    for q in load_questions():
        for field in ["image", "answer_image"]:
            value = q.get(field)
            if value:
                assert (ROOT / value).exists(), f"Missing image: {value}"
