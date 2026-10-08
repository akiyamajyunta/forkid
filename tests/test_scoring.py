from __future__ import annotations

from unittest.mock import patch

from kidgame.data.models import Difficulty
from kidgame.system.scoring import points_for_correct_answer


def test_faster_answers_score_higher() -> None:
    fast = points_for_correct_answer(3.0, Difficulty.EASY)
    slow = points_for_correct_answer(40.0, Difficulty.EASY)
    assert fast > slow


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
