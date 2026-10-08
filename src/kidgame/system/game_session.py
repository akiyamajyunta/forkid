from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import StrEnum, auto

from kidgame.data.models import Difficulty
from kidgame.data.question_runtime import PlayQuestion
from kidgame.system.scoring import points_for_correct_answer
from kidgame.system.config import (
    BONUS_FILL_FAST,
    BONUS_FILL_MID,
    BONUS_FILL_SLOW,
    BONUS_FAST_SEC,
    BONUS_GAUGE_MAX,
    BONUS_MID_SEC,
    CORRECT_TO_CLEAR,
    FEEDBACK_DURATION_SEC,
    INITIAL_BOMB_STOCK,
    INITIAL_LIVES,
    RULES_BY_DIFFICULTY,
    STAR_GAUGE_MAX,
)
from kidgame.system.options_view import OptionsView


class SessionPhase(StrEnum):
    PLAYING = auto()
    FEEDBACK = auto()
    WON = auto()
    LOST = auto()


class LossReason(StrEnum):
    NO_LIVES = auto()
    TIME_UP = auto()


@dataclass
class AnswerFeedback:
    was_correct: bool
    selected_index: int
    correct_index: int
    hint: str


@dataclass
class GameSession:
    difficulty: Difficulty
    questions: list[PlayQuestion]
    lives: int = INITIAL_LIVES
    correct_count: int = 0
    score: int = 0
    last_points_gained: int = 0
    bomb_stock: int = INITIAL_BOMB_STOCK
    bonus_gauge: float = 0.0
    time_remaining: float | None = None
    question_index: int = 0
    phase: SessionPhase = SessionPhase.PLAYING
    loss_reason: LossReason | None = None
    options_view: OptionsView | None = None
    cursor: int = 0
    _question_started_at: float = field(default_factory=time.monotonic)
    _feedback_until: float = 0.0
    _last_feedback: AnswerFeedback | None = None
    _rng: random.Random = field(default_factory=random.Random)

    @classmethod
    def start(
        cls,
        difficulty: Difficulty,
        questions: list[PlayQuestion],
        *,
        seed: int | None = None,
    ) -> GameSession:
        rules = RULES_BY_DIFFICULTY[difficulty]
        session = cls(
            difficulty=difficulty,
            questions=list(questions),
            time_remaining=rules.time_limit_seconds,
        )
        if seed is not None:
            session._rng = random.Random(seed)
        session._begin_question()
        return session

    @property
    def rules(self):
        return RULES_BY_DIFFICULTY[self.difficulty]

    @property
    def current_question(self) -> PlayQuestion | None:
        if self.question_index >= len(self.questions):
            return None
        return self.questions[self.question_index]

    @property
    def last_feedback(self) -> AnswerFeedback | None:
        return self._last_feedback

    @property
    def show_playing_hint(self) -> bool:
        """その問題の残り時間が制限の半分以下でヒント表示（イージーは常に非表示）。"""
        if self.phase is not SessionPhase.PLAYING:
            return False
        limit = self.rules.time_limit_seconds
        if limit is None or self.time_remaining is None:
            return False
        return self.time_remaining <= limit / 2

    @property
    def current_hint(self) -> str:
        q = self.current_question
        return q.hint if q else ""

    def tick(self, dt: float) -> None:
        if self.phase is SessionPhase.PLAYING and self.time_remaining is not None:
            self.time_remaining = max(0.0, self.time_remaining - dt)
            if self.time_remaining <= 0:
                self._lose(LossReason.TIME_UP)
        elif self.phase is SessionPhase.FEEDBACK:
            if time.monotonic() >= self._feedback_until:
                self._advance_after_feedback()

    def move_cursor(self, delta: int) -> None:
        if self.phase is not SessionPhase.PLAYING or self.options_view is None:
            return
        entries = self.options_view.visible_entries()
        if not entries:
            return
        self.cursor = (self.cursor + delta) % len(entries)

    def confirm_answer(self) -> AnswerFeedback | None:
        if self.phase is not SessionPhase.PLAYING or self.options_view is None:
            return None
        entries = self.options_view.visible_entries()
        if not entries:
            return None
        selected_index = entries[self.cursor][0]
        return self._resolve_answer(selected_index)

    def use_bomb(self) -> bool:
        if self.phase is not SessionPhase.PLAYING or self.options_view is None:
            return False
        if self.bomb_stock <= 0:
            return False
        removed = self.options_view.apply_bomb(rng=self._rng)
        if removed <= 0:
            return False
        self.bomb_stock -= 1
        entries = self.options_view.visible_entries()
        if entries:
            self.cursor = min(self.cursor, len(entries) - 1)
        return True

    def _resolve_answer(self, selected_index: int) -> AnswerFeedback:
        assert self.options_view is not None
        q = self.options_view.question
        was_correct = selected_index == q.answer_index
        feedback = AnswerFeedback(
            was_correct=was_correct,
            selected_index=selected_index,
            correct_index=q.answer_index,
            hint=q.hint,
        )
        self._last_feedback = feedback

        if was_correct:
            self.correct_count += 1
            elapsed = time.monotonic() - self._question_started_at
            gained = points_for_correct_answer(elapsed, self.difficulty)
            self.score += gained
            self.last_points_gained = gained
            self._add_bonus_for_speed()
            if self.correct_count >= CORRECT_TO_CLEAR:
                self.phase = SessionPhase.WON
                return feedback
        else:
            self.lives -= 1
            if self.lives <= 0:
                self.phase = SessionPhase.FEEDBACK
                self._feedback_until = time.monotonic() + FEEDBACK_DURATION_SEC
                return feedback

        self.phase = SessionPhase.FEEDBACK
        self._feedback_until = time.monotonic() + FEEDBACK_DURATION_SEC
        return feedback

    def _add_bonus_for_speed(self) -> None:
        elapsed = time.monotonic() - self._question_started_at
        if elapsed <= BONUS_FAST_SEC:
            fill = BONUS_FILL_FAST
        elif elapsed <= BONUS_MID_SEC:
            fill = BONUS_FILL_MID
        else:
            fill = BONUS_FILL_SLOW
        self.bonus_gauge = min(BONUS_GAUGE_MAX, self.bonus_gauge + fill)
        if self.bonus_gauge >= BONUS_GAUGE_MAX:
            self.bonus_gauge = 0.0
            self.bomb_stock = min(STAR_GAUGE_MAX, self.bomb_stock + 1)

    def _advance_after_feedback(self) -> None:
        if self.lives <= 0 and self.phase is SessionPhase.FEEDBACK:
            self._lose(LossReason.NO_LIVES)
            return
        if self.phase is SessionPhase.WON:
            return
        feedback = self._last_feedback
        if feedback is not None and not feedback.was_correct:
            self.phase = SessionPhase.PLAYING
            self._retry_same_question()
            return
        self.question_index += 1
        if self.question_index >= len(self.questions):
            if self.correct_count >= CORRECT_TO_CLEAR:
                self.phase = SessionPhase.WON
            else:
                self._lose(LossReason.NO_LIVES)
            return
        self.phase = SessionPhase.PLAYING
        self._begin_question()

    def _begin_question(self) -> None:
        q = self.current_question
        if q is None:
            return
        self.options_view = OptionsView.fresh(q)
        self.cursor = 0
        self._question_started_at = time.monotonic()
        self.time_remaining = self.rules.time_limit_seconds

    def _retry_same_question(self) -> None:
        """不正解後の再挑戦。ボムで消した選択肢は維持し、タイマーだけリセット。"""
        if self.options_view is None:
            q = self.current_question
            if q is None:
                return
            self.options_view = OptionsView.fresh(q)
        self._question_started_at = time.monotonic()
        self.time_remaining = self.rules.time_limit_seconds
        entries = self.options_view.visible_entries()
        if entries:
            self.cursor = min(self.cursor, len(entries) - 1)
        else:
            self.cursor = 0

    def _lose(self, reason: LossReason) -> None:
        self.phase = SessionPhase.LOST
        self.loss_reason = reason
