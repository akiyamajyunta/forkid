from __future__ import annotations

from unittest.mock import patch

import pytest

from kidgame.data.models import Difficulty
from kidgame.data.question_runtime import PlayQuestion, resolve_for_play
from kidgame.data.models import Question
from kidgame.system.game_session import GameSession, LossReason, SessionPhase
from kidgame.system.options_view import OptionsView


def _bank_q(qid: str = "t", levels: frozenset[Difficulty] | None = None) -> Question:
    return Question(
        id=qid,
        levels=levels or frozenset({Difficulty.EASY, Difficulty.NORMAL, Difficulty.HARD}),
        question="test?",
        options=tuple(f"opt{i}" for i in range(6)),
        answer_index=0,
        hint="hint",
    )


def _play(mode: Difficulty = Difficulty.EASY, qid: str = "t") -> PlayQuestion:
    return resolve_for_play(_bank_q(qid), mode, rng=__import__("random").Random(1))


def test_bomb_removes_half_wrong_options() -> None:
    pq = _play(Difficulty.EASY)
    view = OptionsView.fresh(pq)
    removed = view.apply_bomb(rng=__import__("random").Random(0))
    assert removed == 1
    assert view.visible_count() == 2


def test_clear_after_ten_correct() -> None:
    questions = [_play(qid=f"q{i}") for i in range(10)]
    session = GameSession.start(Difficulty.EASY, questions, seed=1)
    for _ in range(9):
        assert session.current_question is not None
        session.cursor = session.current_question.answer_index
        session.confirm_answer()
        assert session.phase is SessionPhase.FEEDBACK
        session._feedback_until = 0.0
        session.tick(0.0)
        assert session.phase is SessionPhase.PLAYING
    session.cursor = session.current_question.answer_index
    session.confirm_answer()
    assert session.phase is SessionPhase.WON


def test_wrong_answer_costs_life() -> None:
    pq = _play(Difficulty.EASY)
    session = GameSession.start(Difficulty.EASY, [pq], seed=1)
    session.options_view = OptionsView.fresh(pq)
    session._resolve_answer(1 if pq.answer_index == 0 else 0)
    assert session.lives == 2


def test_playing_hint_when_half_time_elapsed() -> None:
    session = GameSession.start(Difficulty.NORMAL, [_play(Difficulty.NORMAL)], seed=1)
    session.time_remaining = 91.0
    assert session.show_playing_hint is False
    session.time_remaining = 90.0
    assert session.show_playing_hint is True


def test_no_playing_hint_on_easy() -> None:
    session = GameSession.start(Difficulty.EASY, [_play()], seed=1)
    assert session.show_playing_hint is False


def test_time_up_triggers_loss() -> None:
    session = GameSession.start(Difficulty.HARD, [_play(Difficulty.HARD)], seed=1)
    session.tick(61.0)
    assert session.phase is SessionPhase.LOST
    assert session.loss_reason is LossReason.TIME_UP


def test_timer_resets_each_question() -> None:
    questions = [_play(Difficulty.HARD, qid=f"q{i}") for i in range(3)]
    session = GameSession.start(Difficulty.HARD, questions, seed=1)
    assert session.time_remaining == 60.0
    session.tick(25.0)
    assert session.time_remaining == 35.0
    assert session.current_question is not None
    session.cursor = session.current_question.answer_index
    session.confirm_answer()
    session._feedback_until = 0.0
    session.tick(0.0)
    assert session.phase is SessionPhase.PLAYING
    assert session.question_index == 1
    assert session.time_remaining == 60.0


def test_bonus_fills_and_grants_bomb() -> None:
    session = GameSession.start(Difficulty.EASY, [_play()], seed=1)
    session.bonus_gauge = 95.0
    with patch("kidgame.system.game_session.time.monotonic", side_effect=[0.0, 1.0]):
        session._question_started_at = 0.0
        session._add_bonus_for_speed()
    assert session.bomb_stock == 1
    assert session.bonus_gauge == 0.0


def test_resolve_for_play_option_counts() -> None:
    q = _bank_q()
    assert len(resolve_for_play(q, Difficulty.EASY, rng=__import__("random").Random(0)).options) == 3
    assert len(resolve_for_play(q, Difficulty.NORMAL, rng=__import__("random").Random(0)).options) == 4
    assert len(resolve_for_play(q, Difficulty.HARD, rng=__import__("random").Random(0)).options) == 6
