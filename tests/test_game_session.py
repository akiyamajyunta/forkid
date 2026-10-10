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


def test_bomb_removals_persist_after_wrong_retry() -> None:
    pq = _play(Difficulty.EASY)
    session = GameSession.start(Difficulty.EASY, [pq], seed=1)
    session.bomb_halves = 2
    assert session.use_bomb()
    hidden = set(session.options_view.hidden_indices if session.options_view else ())
    assert hidden
    wrong = 1 if pq.answer_index == 0 else 0
    session._resolve_answer(wrong)
    session._feedback_until = 0.0
    session.tick(0.0)
    assert session.options_view is not None
    assert session.options_view.hidden_indices == hidden


def test_wrong_answer_stays_on_same_question() -> None:
    questions = [_play(qid=f"q{i}") for i in range(3)]
    session = GameSession.start(Difficulty.EASY, questions, seed=1)
    pq = session.current_question
    assert pq is not None
    wrong = 1 if pq.answer_index == 0 else 0
    session._resolve_answer(wrong)
    assert session.phase is SessionPhase.FEEDBACK
    session._feedback_until = 0.0
    session.tick(0.0)
    assert session.phase is SessionPhase.PLAYING
    assert session.question_index == 0
    assert session.current_question is questions[0]


def test_clear_with_lives_remaining() -> None:
    questions = [_play(qid=f"q{i}") for i in range(10)]
    session = GameSession.start(Difficulty.EASY, questions, seed=1)
    pq = session.current_question
    assert pq is not None
    wrong = 1 if pq.answer_index == 0 else 0
    session._resolve_answer(wrong)
    session._feedback_until = 0.0
    session.tick(0.0)
    assert session.lives == 2
    for i in range(10):
        assert session.current_question is not None
        entries = session.options_view.visible_entries() if session.options_view else []
        pick = next(
            ci for ci, (idx, _) in enumerate(entries) if idx == session.current_question.answer_index
        )
        session.cursor = pick
        session.confirm_answer()
        if session.phase is SessionPhase.WON:
            break
        session._feedback_until = 0.0
        session.tick(0.0)
    assert session.phase is SessionPhase.WON
    assert session.lives > 0
    assert session.correct_count == 10


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


def test_skill_gain_half_within_10s() -> None:
    session = GameSession.start(Difficulty.EASY, [_play()], seed=1)
    assert session.bomb_halves == 2
    session._question_started_at = 0.0
    with patch("kidgame.system.game_session.time.monotonic", return_value=5.0):
        session._add_skill_on_fast_answer()
    assert session.bomb_halves == 3


def test_skill_no_gain_over_10s() -> None:
    session = GameSession.start(Difficulty.EASY, [_play()], seed=1)
    session._question_started_at = 0.0
    with patch("kidgame.system.game_session.time.monotonic", return_value=11.0):
        session._add_skill_on_fast_answer()
    assert session.bomb_halves == 2


def test_session_initial_star_stats() -> None:
    session = GameSession.start(Difficulty.EASY, [_play()], seed=1)
    assert session.lives == 3
    assert session.bomb_halves == 2


def test_resolve_for_play_option_counts() -> None:
    q = _bank_q()
    assert len(resolve_for_play(q, Difficulty.EASY, rng=__import__("random").Random(0)).options) == 3
    assert len(resolve_for_play(q, Difficulty.NORMAL, rng=__import__("random").Random(0)).options) == 4
    assert len(resolve_for_play(q, Difficulty.HARD, rng=__import__("random").Random(0)).options) == 6
