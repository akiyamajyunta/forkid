"""正解時の得点計算（速さ × 難易度）。"""

from __future__ import annotations

from kidgame.data.models import Difficulty

SCORE_BASE = 1000
SCORE_MIN = 100

_DIFFICULTY_MULT: dict[Difficulty, float] = {
    Difficulty.EASY: 1.0,
    Difficulty.NORMAL: 1.6,
    Difficulty.HARD: 2.4,
}


def _speed_factor(elapsed_sec: float) -> float:
    if elapsed_sec <= 5.0:
        return 1.0
    if elapsed_sec <= 12.0:
        return 0.78
    if elapsed_sec <= 20.0:
        return 0.58
    if elapsed_sec <= 35.0:
        return 0.42
    return 0.30


def points_for_correct_answer(elapsed_sec: float, difficulty: Difficulty) -> int:
    """早く解くほど高く、難易度が高いほど高い。"""
    mult = _DIFFICULTY_MULT[difficulty]
    raw = SCORE_BASE * _speed_factor(elapsed_sec) * mult
    return max(SCORE_MIN, int(raw))
