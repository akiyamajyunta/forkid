from __future__ import annotations

from dataclasses import dataclass

from kidgame.data.models import Difficulty

CORRECT_TO_CLEAR = 10
INITIAL_LIVES = 3
INITIAL_BOMB_STOCK = 1
STAR_GAUGE_MAX = 7
# 技能（ボム）：問題開始からこの秒数以内の正解で星半分（0.5）増える
SKILL_GAIN_TIME_SEC = 10.0
SKILL_GAIN_HALF_STARS = 1

FEEDBACK_DURATION_SEC = 1.2


@dataclass(frozen=True, slots=True)
class DifficultyRules:
    time_limit_seconds: float | None
    label: str

    @property
    def has_timer(self) -> bool:
        return self.time_limit_seconds is not None


RULES_BY_DIFFICULTY: dict[Difficulty, DifficultyRules] = {
    Difficulty.EASY: DifficultyRules(time_limit_seconds=None, label="イージー"),
    Difficulty.NORMAL: DifficultyRules(time_limit_seconds=180.0, label="ノーマル"),
    Difficulty.HARD: DifficultyRules(time_limit_seconds=60.0, label="ハード"),
}

DIFFICULTY_LABEL_EN: dict[Difficulty, str] = {
    Difficulty.EASY: "EASY",
    Difficulty.NORMAL: "NORMAL",
    Difficulty.HARD: "HARD",
}


def bomb_eliminate_count(option_count: int) -> int:
    """README_SYSTEM: 選択肢数の半分（切り捨て）だけ誤答を除外。"""
    return option_count // 2
