"""星蓮船風の右ステータス欄描画。"""

from __future__ import annotations

import pygame

from kidgame.system.config import CORRECT_TO_CLEAR, DIFFICULTY_LABEL_EN, INITIAL_LIVES
from kidgame.system.game_session import GameSession
from kidgame.ui.draw_helpers import blit_centered_outlined, blit_outlined, draw_star_row
from kidgame.ui.layout import ScreenLayout
from kidgame.ui.theme import COLOR_CURSOR, COLOR_GAUGE_TIMER, COLOR_TEXT


def draw_status_sidebar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    session: GameSession,
    high_score: int,
    display_score: int,
    L: ScreenLayout,
    label_font: pygame.font.Font,
    value_font: pygame.font.Font,
    small_font: pygame.font.Font,
    mode_font: pygame.font.Font,
) -> None:
    mode_en = DIFFICULTY_LABEL_EN[session.difficulty]
    blit_centered_outlined(
        surface,
        mode_font,
        mode_en,
        rect.centerx,
        rect.y + L.y(18),
        COLOR_CURSOR,
    )

    x = rect.x + L.x(12)
    y = rect.y + L.y(52)
    line = L.y(34)

    blit_outlined(surface, label_font, "最高得点", x, y, COLOR_TEXT)
    y += line
    blit_outlined(
        surface,
        value_font,
        f"{high_score:,}",
        x,
        y,
        COLOR_TEXT,
    )
    y += line + L.y(8)

    blit_outlined(surface, label_font, "得点", x, y, COLOR_TEXT)
    y += line
    blit_outlined(
        surface,
        value_font,
        f"{display_score:,}",
        x,
        y,
        COLOR_CURSOR,
    )
    y += line + L.y(12)

    blit_outlined(surface, label_font, "正解", x, y, COLOR_TEXT)
    y += line
    blit_outlined(
        surface,
        value_font,
        f"{session.correct_count} / {CORRECT_TO_CLEAR}",
        x,
        y,
        COLOR_TEXT,
    )
    y += line + L.y(12)

    blit_outlined(surface, label_font, "答力 :", x, y, COLOR_TEXT)
    draw_star_row(
        surface,
        x + L.x(72),
        y + L.y(2),
        filled=session.lives,
        total=INITIAL_LIVES,
        size=L.y(16),
    )
    y += line + L.y(4)

    blit_outlined(surface, label_font, "技能 :", x, y, COLOR_TEXT)
    bomb_slots = 3
    draw_star_row(
        surface,
        x + L.x(72),
        y + L.y(2),
        filled=min(session.bomb_stock, bomb_slots),
        total=bomb_slots,
        size=L.y(16),
    )
    y += line + L.y(12)

    blit_outlined(surface, label_font, "時間", x, y, COLOR_TEXT)
    y += L.y(26)
    bar_w = rect.width - L.x(28)
    bar_h = max(8, L.y(14))
    bar = pygame.Rect(x, y, bar_w, bar_h)
    pygame.draw.rect(surface, (20, 24, 32), bar, border_radius=2)
    pygame.draw.rect(surface, (0, 0, 0), bar, width=2, border_radius=2)
    ratio = _time_ratio(session)
    if ratio > 0:
        fill = bar.copy()
        fill.width = max(2, int(bar.width * ratio))
        pygame.draw.rect(surface, COLOR_GAUGE_TIMER, fill, border_radius=2)

def _time_ratio(session: GameSession) -> float:
    limit = session.rules.time_limit_seconds
    if limit is None or session.time_remaining is None:
        return 1.0
    return max(0.0, min(1.0, session.time_remaining / limit))
