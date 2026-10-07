from __future__ import annotations

import pygame

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
        # 本文に対して約 55%（Excel のルビに近い比率）
        self.ruby = pygame.font.SysFont(name, max(9, sz(14)))
        self.furigana = pygame.font.SysFont(name, max(10, sz(18)))
