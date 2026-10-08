from __future__ import annotations

import random

from kidgame.data.distractors import (
    build_six_options,
    extract_dai_keyword,
    question_wants_food_distractors,
)


def test_extract_dai_keyword() -> None:
    assert extract_dai_keyword("サイはサイでもおかいもの") == "サイ"


def test_food_question_detected() -> None:
    assert question_wants_food_distractors("たべるのに １０びょうまたされるものって な〜んだ？")


def test_dai_distractors_share_keyword() -> None:
    pool = [
        "サイコ",
        "サイド",
        "さいふ",
        "お買い物サイ",
        "えんぴつ",
        "くつ",
        "まど",
        "でんわ",
        "はさみ",
        "ぞう",
    ]
    q = "サイはサイでも おかいものに わすれてはいけないサイは な〜んだ？"
    answer = "お買い物サイ"
    rng = random.Random(1)
    options, idx = build_six_options(q, answer, pool, rng)
    wrong = [o for i, o in enumerate(options) if i != idx]
    assert sum(1 for w in wrong if "サイ" in w) >= 2


def test_fix_correct_at_a() -> None:
    pool = ["りんご", "みかん", "うどん", "パン", "くつ", "まど"]
    options, idx = build_six_options(
        "たべもの?", "うどん", pool, random.Random(0), fix_correct_at_a=True
    )
    assert idx == 0
    assert options[0] == "うどん"


def test_food_distractors() -> None:
    pool = [
        "りんご",
        "みかん",
        "うどん",
        "パン",
        "でんわ",
        "くつ",
        "まど",
        "はさみ",
        "ぞう",
        "えんぴつ",
    ]
    q = "たべるのに １０びょうまたされるものって な〜んだ？"
    answer = "うどん"
    rng = random.Random(2)
    options, idx = build_six_options(q, answer, pool, rng)
    wrong = [o for i, o in enumerate(options) if i != idx]
    foodish = sum(1 for w in wrong if w in {"りんご", "みかん", "パン"})
    assert foodish >= 2
