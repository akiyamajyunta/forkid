from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

_KANJI_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")


@dataclass(frozen=True, slots=True)
class RubySegment:
    text: str
    reading: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> RubySegment:
        return cls(
            text=str(raw.get("text", "")),
            reading=str(raw.get("read", raw.get("reading", ""))),
        )


def contains_kanji(text: str) -> bool:
    return _KANJI_RE.search(text) is not None


def parse_ruby_list(raw: Any) -> tuple[RubySegment, ...] | None:
    if not raw:
        return None
    if not isinstance(raw, list):
        raise ValueError("ruby must be an array")
    return tuple(RubySegment.from_dict(item) for item in raw)


def parse_options_ruby(raw: Any, option_count: int) -> tuple[tuple[RubySegment, ...], ...] | None:
    if not raw:
        return None
    if not isinstance(raw, list) or len(raw) != option_count:
        raise ValueError("options_ruby must be an array with the same length as options")
    result: list[tuple[RubySegment, ...]] = []
    for item in raw:
        if item is None:
            result.append(())
        elif isinstance(item, list):
            result.append(tuple(RubySegment.from_dict(x) for x in item))
        else:
            raise ValueError("each options_ruby entry must be an array of segments")
    return tuple(result)


@lru_cache(maxsize=512)
def _kakasi_convert(text: str) -> tuple[dict[str, str], ...]:
    from pykakasi import kakasi

    kks = kakasi()
    return tuple(kks.convert(text))


@lru_cache(maxsize=512)
def to_hiragana_line(text: str) -> str:
    if not contains_kanji(text):
        return ""
    return "".join(part["hira"] for part in _kakasi_convert(text))


@lru_cache(maxsize=512)
def auto_ruby_segments(text: str) -> tuple[RubySegment, ...] | None:
    """漢字を含む文を、Excel のルビのように上付き読み用セグメントに分割する。"""
    if not contains_kanji(text):
        return None
    segments: list[RubySegment] = []
    for part in _kakasi_convert(text):
        orig = part["orig"]
        if not orig:
            continue
        reading = part["hira"] if contains_kanji(orig) else ""
        segments.append(RubySegment(orig, reading))
    return tuple(segments) if segments else None


def segments_or_reading_line(
    text: str,
    ruby: tuple[RubySegment, ...] | None,
) -> tuple[tuple[RubySegment, ...] | None, str]:
    """手動ルビがあればそれを優先。なければ漢字を上付きルビで自動分割。"""
    if ruby:
        return ruby, ""
    auto = auto_ruby_segments(text)
    if auto:
        return auto, ""
    return None, ""
