"""正解時の得点計算（速さ × 難易度）。"""

from __future__ import annotations

from kidgame.data.models import Difficulty

SCORE_BASE = 1000
SCORE_MIN = 100

# 経過秒 0 で満点係数、TIER_END 秒で最低係数（1秒刻み＋秒内は線形補間）
_SPEED_MIN_FACTOR = 0.25
_SPEED_TIER_END_SEC = 60

_DIFFICULTY_MULT: dict[Difficulty, float] = {
    Difficulty.EASY: 1.0,
    Difficulty.NORMAL: 1.6,
    Difficulty.HARD: 2.4,
}


def speed_factor(elapsed_sec: float) -> float:
    """早いほど 1.0 に近い。0〜60秒を細かく線形で下げ、60秒以降は最低。"""
    elapsed = max(0.0, elapsed_sec)
    sec = int(elapsed)
    if sec >= _SPEED_TIER_END_SEC:
        return _SPEED_MIN_FACTOR
    frac = elapsed - sec
    f0 = _factor_at_whole_second(sec)
    f1 = _factor_at_whole_second(sec + 1)
    return f0 + (f1 - f0) * frac


def _factor_at_whole_second(second: int) -> float:
    second = max(0, min(second, _SPEED_TIER_END_SEC))
    t = second / _SPEED_TIER_END_SEC
    return _SPEED_MIN_FACTOR + (1.0 - _SPEED_MIN_FACTOR) * (1.0 - t)


def points_for_correct_answer(elapsed_sec: float, difficulty: Difficulty) -> int:
    """早く解くほど高く、難易度が高いほど高い（経過時間は秒単位で細かく反映）。"""
    mult = _DIFFICULTY_MULT[difficulty]
    raw = SCORE_BASE * speed_factor(elapsed_sec) * mult
    return max(SCORE_MIN, int(raw))
