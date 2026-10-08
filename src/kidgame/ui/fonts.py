from __future__ import annotations

import os
from pathlib import Path

import pygame

_HGS_POP_SYS_NAMES = (
    "hgp創英角ポップ体pro",
    "hgg創英角ポップ体pro",
    "hg創英角ポップ体pro",
    "hgs創英角ポップ体",
    "hg創英角ﾎﾟｯﾌﾟ体",
    "hg創英角ポップ体",
)

_FONT_CANDIDATES = (
    "yugothicui",
    "yugothic",
    "meiryo",
    "msgothic",
    "msmincho",
    "notosansjp",
)


def _pick_font_name() -> str | None:
    pygame.font.init()
    names = {n.lower() for n in pygame.font.get_fonts()}
    for candidate in _FONT_CANDIDATES:
        if candidate in names:
            return candidate
    return None


def _find_hgs_pop_file() -> Path | None:
    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    if not fonts_dir.is_dir():
        return None
    for pattern in ("HGRP*.TTC", "HGRP*.TTF", "HGRSKP*.TTC", "HGSKP*.TTF"):
        for path in sorted(fonts_dir.glob(pattern)):
            return path
    return None


def _load_difficulty_font(size: int) -> pygame.font.Font:
    pygame.font.init()
    path = _find_hgs_pop_file()
    if path is not None:
        try:
            return pygame.font.Font(str(path), size)
        except (OSError, pygame.error):
            pass
    names = {n.lower(): n for n in pygame.font.get_fonts()}
    for candidate in _HGS_POP_SYS_NAMES:
        key = candidate.lower()
        if key in names:
            return pygame.font.SysFont(names[key], size, bold=True)
    fallback = _pick_font_name()
    return pygame.font.SysFont(fallback, size, bold=True)


class FontSet:
    def __init__(self, scale: float = 1.0) -> None:
        name = _pick_font_name()
        s = max(0.55, scale)

        def sz(base: int) -> int:
            return max(11, int(base * s))

        self.title = pygame.font.SysFont(name, sz(52), bold=True)
        self.heading = pygame.font.SysFont(name, sz(32), bold=True)
        self.body = pygame.font.SysFont(name, sz(26))
        self.small = pygame.font.SysFont(name, sz(20))
        self.option = pygame.font.SysFont(name, sz(28))
        self.status = pygame.font.SysFont(name, sz(22), bold=True)
        self.score_label = pygame.font.SysFont(name, sz(20), bold=True)
        self.score_value = pygame.font.SysFont(name, sz(26), bold=True)
        self.difficulty_mode = _load_difficulty_font(sz(34))
        # 本文に対して約 55%（Excel のルビに近い比率）
        self.ruby = pygame.font.SysFont(name, max(9, sz(14)))
        self.furigana = pygame.font.SysFont(name, max(10, sz(18)))
