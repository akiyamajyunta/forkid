"""星蓮船風の右ステータス欄描画。"""

from __future__ import annotations

import pygame

from kidgame.system.config import (
    CORRECT_TO_CLEAR,
    DIFFICULTY_LABEL_EN,
    STAR_GAUGE_MAX,
)
from kidgame.system.game_session import GameSession
from kidgame.ui.draw_helpers import (
    STAR_ROW_GAP_OVERLAP,
    scale_star_sprite,
    blit_centered_outlined,
    blit_outlined,
    blit_right_outlined,
    draw_star_row_right,
    draw_star_row_right_sprites,
    star_row_width,
    star_sprite_row_width,
)
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
    star_filled: pygame.Surface | None = None,
    star_empty: pygame.Surface | None = None,
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
    right_x = rect.right - L.x(12)
    y = rect.y + L.y(52)
    line = L.y(34)

    blit_outlined(surface, label_font, "最高得点", x, y, COLOR_TEXT)
    y += line
    blit_right_outlined(
        surface,
        value_font,
        f"{high_score:,}",
        right_x,
        y,
        COLOR_TEXT,
    )
    y += line + L.y(8)

    blit_outlined(surface, label_font, "得点", x, y, COLOR_TEXT)
    y += line
    blit_right_outlined(
        surface,
        value_font,
        f"{display_score:,}",
        right_x,
        y,
        COLOR_CURSOR,
    )
    y += line + L.y(12)

    blit_outlined(surface, label_font, "正解", x, y, COLOR_TEXT)
    y += line
    blit_right_outlined(
        surface,
        value_font,
        f"{session.correct_count} / {CORRECT_TO_CLEAR}",
        right_x,
        y,
        COLOR_TEXT,
    )
    y += line + L.y(12)

    star_avail_w = max(1, right_x - x)
    star_height = max(8, int(round(L.y(13) * 1.5)))
    star_gap = STAR_ROW_GAP_OVERLAP
    use_sprites = star_filled is not None and star_empty is not None

    if use_sprites:
        while star_height > 8:
            sw = scale_star_sprite(star_filled, star_height).get_width()
            need = star_sprite_row_width(STAR_GAUGE_MAX, sw, star_gap)
            if need <= star_avail_w:
                break
            star_height -= 1
    else:
        while star_height > 8:
            need = star_row_width(STAR_GAUGE_MAX, star_height, star_gap)
            if need <= star_avail_w:
                break
            star_height -= 1

    def _draw_stars(filled: int) -> None:
        if use_sprites and star_filled is not None and star_empty is not None:
            draw_star_row_right_sprites(
                surface,
                right_x,
                y + L.y(2),
                filled=filled,
                total=STAR_GAUGE_MAX,
                height=star_height,
                star_on=star_filled,
                star_off=star_empty,
                gap=star_gap,
            )
        else:
            draw_star_row_right(
                surface,
                right_x,
                y + L.y(2),
                filled=filled,
                total=STAR_GAUGE_MAX,
                size=star_height,
                gap=star_gap,
            )

    blit_outlined(surface, label_font, "答力 :", x, y, COLOR_TEXT)
    _draw_stars(min(session.lives, STAR_GAUGE_MAX))
    y += line + L.y(4)

    blit_outlined(surface, label_font, "技能 :", x, y, COLOR_TEXT)
    _draw_stars(min(session.bomb_stock, STAR_GAUGE_MAX))
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
