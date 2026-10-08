from __future__ import annotations

import random

from kidgame.data.distractors import build_six_options
from kidgame.data.kid_language import is_kid_friendly_distractor


def test_blocks_adult_distractors() -> None:
    assert not is_kid_friendly_distractor("Gメン／万引きGメン")
    assert not is_kid_friendly_distractor("まずホップが大事です")


def test_kid_build_avoids_blocked_pool() -> None:
    pool = [
        "ゴメン",
        "マテ茶",
        "Gメン／万引きGメン",
        "まずホップが大事です",
        "りんご",
        "みかん",
        "うさぎ",
        "ねこ",
        "ぞう",
        "くつ",
    ]
    q = "メンはメンでも わるいことをしたときに くちからでるメン な〜んだ？"
    options, idx = build_six_options(q, "ゴメン", pool, random.Random(0), for_kids=True)
    wrong = [o for i, o in enumerate(options) if i != idx]
    assert "Gメン" not in "".join(wrong)
    assert "ホップ" not in "".join(wrong)
