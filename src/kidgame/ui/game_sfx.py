"""効果音の読み込みと再生。"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pygame

# 正解時: interval 秒おきに count 回（「かたかたかたっ」）
SCORE_BURST_COUNT = 10
SCORE_BURST_INTERVAL_SEC = 0.1
def score_burst_duration_sec() -> float:
    return SCORE_BURST_COUNT * SCORE_BURST_INTERVAL_SEC


def _sfx_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "assets" / "sfx"


def _ensure_mixer() -> bool:
    if pygame.mixer.get_init():
        return True
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=8, buffer=512)
        return True
    except pygame.error:
        return False


def _load_sound(path: Path) -> pygame.mixer.Sound | None:
    if not path.is_file():
        return None
    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error:
        return None


@dataclass(frozen=True, slots=True)
class GameSfx:
    cursor_move: pygame.mixer.Sound | None
    score_tick: pygame.mixer.Sound | None
    miss: pygame.mixer.Sound | None

    def play_cursor_move(self) -> None:
        self._play(self.cursor_move)

    def play_miss(self) -> None:
        self._play(self.miss)

    def play_score_tick(self) -> None:
        """正解得点用の短いクリック音（重ね再生可）。"""
        if self.score_tick is None:
            return
        try:
            channel = pygame.mixer.find_channel(True)
            if channel is not None:
                channel.play(self.score_tick)
            else:
                self.score_tick.play()
        except pygame.error:
            pass

    @staticmethod
    def _play(sound: pygame.mixer.Sound | None) -> None:
        if sound is None:
            return
        try:
            sound.play()
        except pygame.error:
            pass


@lru_cache(maxsize=1)
def load_game_sfx() -> GameSfx:
    base = _sfx_dir()
    if not _ensure_mixer():
        return GameSfx(cursor_move=None, score_tick=None, miss=None)
    return GameSfx(
        cursor_move=_load_sound(base / "cursor_move.mp3"),
        score_tick=_load_sound(base / "score_tick.mp3"),
        miss=_load_sound(base / "miss_punch.mp3"),
    )
