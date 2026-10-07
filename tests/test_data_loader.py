from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from kidgame.data.loader import QuestionRepository, load_questions_file
from kidgame.data.models import Difficulty, Question, QuestionBank

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
QUESTIONS_JSON = DATA_DIR / "questions.json"


def test_load_default_questions_file() -> None:
    bank = load_questions_file(QUESTIONS_JSON)
    assert len(bank.questions) >= 100
    for d in Difficulty:
        assert len(bank.for_mode(d)) >= 10
    assert bank.questions[0].dev_explanation
    assert "答えの 最初" not in bank.questions[0].hint


def test_question_validation_too_few_options() -> None:
    with pytest.raises(ValueError, match="options length"):
        Question.from_dict(
            {
                "id": "bad",
                "levels": ["easy"],
                "question": "q",
                "options": ["a", "b"],
                "answer_index": 0,
            }
        )


def test_levels_overlap_pool() -> None:
    bank = load_questions_file(QUESTIONS_JSON)
    easy_ids = {q.id for q in bank.for_mode(Difficulty.EASY)}
    normal_ids = {q.id for q in bank.for_mode(Difficulty.NORMAL)}
    assert easy_ids & normal_ids


def test_repository_draw_removes_from_pool() -> None:
    repo = QuestionRepository.from_file(QUESTIONS_JSON)
    rng = random.Random(42)
    first = repo.draw(Difficulty.EASY, 3, rng=rng)
    assert len(first) == 3
    assert len({q.id for q in first}) == 3
    remaining = repo.available_count(Difficulty.EASY)
    assert remaining == repo.peek_all(Difficulty.EASY).__len__()


def test_repository_insufficient_pool() -> None:
    payload = {
        "questions": [
            {
                "id": "easy_only",
                "levels": ["easy"],
                "question": "test?",
                "options": ["a", "b", "c", "d", "e", "f"],
                "answer_index": 0,
            }
        ]
    }
    bank = QuestionBank.from_dict(payload)
    repo = QuestionRepository(bank)
    with pytest.raises(ValueError, match="Not enough"):
        repo.draw(Difficulty.EASY, 10)


def test_duplicate_id_rejected(tmp_path: Path) -> None:
    payload = {
        "questions": [
            {
                "id": "dup",
                "levels": ["easy"],
                "question": "q1?",
                "options": ["a", "b", "c", "d", "e", "f"],
                "answer_index": 0,
            },
            {
                "id": "dup",
                "levels": ["easy"],
                "question": "q2?",
                "options": ["a", "b", "c", "d", "e", "f"],
                "answer_index": 1,
            },
        ]
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_questions_file(path)
