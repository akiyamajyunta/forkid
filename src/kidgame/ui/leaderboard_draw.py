"""ランキング表の描画（画面幅いっぱい）。"""

from __future__ import annotations

import pygame

from kidgame.system.leaderboard import (
    LEADERBOARD_SIZE,
    is_placeholder,
    padded_entries,
    row_display,
)
from kidgame.ui.draw_helpers import blit_outlined, blit_right_outlined
from kidgame.ui.layout import ScreenLayout
from kidgame.ui.theme import COLOR_CURSOR, COLOR_TEXT, COLOR_TEXT_DIM


def _column_x(
    L: ScreenLayout,
    area: pygame.Rect | None = None,
) -> tuple[int, int, int, int, int]:
    """順位左端, 名前, 得点, 日時, 正答率右端。"""
    if area is None:
        left = L.x(16)
        rank_x = left
        name_x = L.x(52)
        score_x = int(L.width * 0.34)
        date_x = int(L.width * 0.56)
        acc_right = L.width - L.x(20)
        return rank_x, name_x, score_x, date_x, acc_right
    rank_x = area.left + L.x(4)
    name_x = area.left + L.x(40)
    score_x = area.left + int(area.width * 0.36)
    date_x = area.left + int(area.width * 0.58)
    acc_right = area.right - L.x(6)
    return rank_x, name_x, score_x, date_x, acc_right


def leaderboard_table_bottom_y(top_y: int, bottom_y: int, L: ScreenLayout) -> int:
    """draw_leaderboard_table と同じ行配置での下端 y。"""
    usable_h = max(L.y(200), bottom_y - top_y)
    row_h = max(L.y(28), usable_h // LEADERBOARD_SIZE)
    return top_y + row_h * LEADERBOARD_SIZE


def draw_leaderboard_table(
    surface: pygame.Surface,
    *,
    entries: list,
    top_y: int,
    bottom_y: int,
    L: ScreenLayout,
    row_font: pygame.font.Font,
    rank_font: pygame.font.Font | None = None,
    highlight_rank: int | None = None,
    content_rect: pygame.Rect | None = None,
) -> int:
    """10行を均等配置して描画し、下端 y を返す。"""
    rows = padded_entries(entries)
    rank_x, name_x, score_x, date_x, acc_right = _column_x(L, content_rect)
    rank_font = rank_font or row_font
    usable_h = max(L.y(200), bottom_y - top_y)
    row_h = max(L.y(28), usable_h // LEADERBOARD_SIZE)

    y = top_y
    for i, entry in enumerate(rows[:LEADERBOARD_SIZE], start=1):
        name, score, played_at, accuracy = row_display(entry)
        filled = not is_placeholder(entry)
        highlighted = highlight_rank is not None and i == highlight_rank
        if highlighted:
            name_color = COLOR_CURSOR
            score_color = COLOR_CURSOR
        else:
            name_color = COLOR_TEXT if filled else COLOR_TEXT_DIM
            score_color = COLOR_CURSOR if filled else COLOR_TEXT_DIM
        rank_color = COLOR_CURSOR if highlighted else COLOR_TEXT_DIM

        blit_outlined(surface, rank_font, f"{i:02d}", rank_x, y, rank_color)
        blit_outlined(surface, row_font, name, name_x, y, name_color)
        blit_outlined(surface, row_font, score, score_x, y, score_color)
        blit_outlined(surface, row_font, played_at, date_x, y, name_color)
        blit_right_outlined(surface, row_font, accuracy, acc_right, y, name_color)
        y += row_h
    return y
