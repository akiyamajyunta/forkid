from __future__ import annotations

from unittest.mock import patch

from kidgame.data.models import Difficulty
from kidgame.system.scoring import points_for_correct_answer, speed_factor


def test_faster_answers_score_higher() -> None:
    fast = points_for_correct_answer(3.0, Difficulty.EASY)
    slow = points_for_correct_answer(40.0, Difficulty.EASY)
    assert fast > slow


def test_points_drop_each_full_second() -> None:
    prev = points_for_correct_answer(0.0, Difficulty.EASY)
    for sec in range(1, 20):
        cur = points_for_correct_answer(float(sec), Difficulty.EASY)
        assert cur < prev
        prev = cur


def test_sub_second_changes_score() -> None:
    sooner = points_for_correct_answer(4.0, Difficulty.EASY)
    later = points_for_correct_answer(4.7, Difficulty.EASY)
    assert sooner > later


def test_speed_factor_no_coarse_cliff_at_five_seconds() -> None:
    """旧5段階だと5秒と6秒で大きく落ちていた境界を、なめらかにする。"""
    at_5 = speed_factor(5.0)
    at_6 = speed_factor(6.0)
    assert at_5 - at_6 < 0.05


def test_harder_difficulty_scores_higher() -> None:
    easy = points_for_correct_answer(4.0, Difficulty.EASY)
    hard = points_for_correct_answer(4.0, Difficulty.HARD)
    assert hard > easy


def test_session_gains_score_on_correct() -> None:
    from kidgame.data.question_runtime import PlayQuestion, resolve_for_play
    from kidgame.data.models import Question
    from kidgame.system.game_session import GameSession

    q = Question(
        id="t",
        levels=frozenset({Difficulty.EASY}),
        question="?",
        options=tuple(f"o{i}" for i in range(6)),
        answer_index=0,
        hint="h",
    )
    pq = resolve_for_play(q, Difficulty.EASY, rng=__import__("random").Random(0))
    session = GameSession.start(Difficulty.EASY, [pq], seed=1)
    entries = session.options_view.visible_entries() if session.options_view else []
    pick = next(i for i, (idx, _) in enumerate(entries) if idx == pq.answer_index)
    with patch(
        "kidgame.system.game_session.time.monotonic",
        side_effect=[0.0, 2.0, 3.0],
    ):
        session._question_started_at = 0.0
        session.cursor = pick
        session.confirm_answer()
    assert session.score > 0
