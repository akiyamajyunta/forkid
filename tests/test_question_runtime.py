from __future__ import annotations

import random

from kidgame.data.models import Difficulty, Question
from kidgame.data.question_runtime import resolve_for_play
from kidgame.ui.option_labels import option_display_letter


def _q() -> Question:
    return Question(
        id="t",
        levels=frozenset({Difficulty.NORMAL}),
        question="?",
        options=("正", "誤1", "誤2", "誤3", "誤4", "誤5"),
        answer_index=0,
        hint="",
    )


def test_resolve_shuffles_correct_position() -> None:
    positions = {
        resolve_for_play(_q(), Difficulty.NORMAL, rng=random.Random(seed)).answer_index
        for seed in range(40)
    }
    assert len(positions) > 1


def test_display_letters_are_sequential_from_top() -> None:
    assert option_display_letter(0) == "A"
    assert option_display_letter(3) == "D"
