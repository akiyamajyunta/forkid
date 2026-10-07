from __future__ import annotations

from kidgame.data.furigana import (
    RubySegment,
    auto_ruby_segments,
    contains_kanji,
    segments_or_reading_line,
    to_hiragana_line,
)
from kidgame.data.models import Question, Difficulty


def test_contains_kanji() -> None:
    assert contains_kanji("食パン")
    assert not contains_kanji("たまご")


def test_to_hiragana_line() -> None:
    line = to_hiragana_line("牛乳")
    assert "ぎゅう" in line


def test_auto_ruby_segments() -> None:
    segs = auto_ruby_segments("牛乳")
    assert segs is not None
    assert any(s.reading for s in segs)
    assert "".join(s.text for s in segs) == "牛乳"


def test_segments_or_reading_line_uses_ruby_above() -> None:
    segs, line = segments_or_reading_line("食パン", None)
    assert segs is not None
    assert line == ""


def test_question_ruby_from_json() -> None:
    q = Question.from_dict(
        {
            "id": "t",
            "levels": ["easy"],
            "question": "test",
            "options": ["a", "b", "c", "d", "e", "f"],
            "answer_index": 0,
            "ruby": [{"text": "食", "read": "た"}],
        }
    )
    assert q.ruby == (RubySegment("食", "た"),)
