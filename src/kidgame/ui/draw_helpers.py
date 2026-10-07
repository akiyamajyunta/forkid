from __future__ import annotations

import pygame

from kidgame.ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_BORDER_GOLD,
    COLOR_CURSOR,
    COLOR_GAUGE_BG,
    COLOR_MAIN_PANEL,
    COLOR_OPTION_FILL,
    COLOR_OPTION_FILL_SEL,
    COLOR_STATUS_INNER,
    COLOR_STATUS_PANEL,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
)


def fill_gradient_v(
    surface: pygame.Surface,
    rect: pygame.Rect,
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> None:
    h = max(1, rect.height)
    for y in range(h):
        t = y / (h - 1) if h > 1 else 0
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        pygame.draw.line(surface, (r, g, b), (rect.x, rect.y + y), (rect.right - 1, rect.y + y))


def draw_orante_frame(surface: pygame.Surface, rect: pygame.Rect, *, thick: int = 4) -> None:
    pygame.draw.rect(surface, COLOR_BORDER_DARK, rect, border_radius=6)
    inner = rect.inflate(-thick * 2, -thick * 2)
    pygame.draw.rect(surface, COLOR_BORDER_GOLD, inner, width=2, border_radius=4)
    corner = 14
    for cx, cy in (
        (inner.left, inner.top),
        (inner.right - 1, inner.top),
        (inner.left, inner.bottom - 1),
        (inner.right - 1, inner.bottom - 1),
    ):
        pygame.draw.circle(surface, COLOR_BORDER_GOLD, (cx, cy), corner // 2, 1)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, *, status: bool = False) -> None:
    if status:
        fill_gradient_v(surface, rect, COLOR_STATUS_PANEL, COLOR_STATUS_INNER)
    else:
        fill_gradient_v(surface, rect, COLOR_MAIN_PANEL, (24, 34, 50))
    draw_orante_frame(surface, rect)


def draw_option_bar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    selected: bool = False,
) -> None:
    """選択肢用の横長ブロック（ワイヤーフレームの選択肢バー）。"""
    fill = COLOR_OPTION_FILL_SEL if selected else COLOR_OPTION_FILL
    pygame.draw.rect(surface, fill, rect, border_radius=5)
    border = COLOR_CURSOR if selected else COLOR_BORDER_DARK
    width = 3 if selected else 2
    pygame.draw.rect(surface, border, rect, width=width, border_radius=5)
    if selected:
        inner = rect.inflate(-width * 2, -width * 2)
        pygame.draw.rect(surface, COLOR_BORDER_GOLD, inner, width=1, border_radius=3)


def draw_gauge(
    surface: pygame.Surface,
    rect: pygame.Rect,
    ratio: float,
    fill_color: tuple[int, int, int],
    label: str,
    font: pygame.font.Font,
) -> None:
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, COLOR_GAUGE_BG, rect, border_radius=3)
    if ratio > 0:
        fill = rect.copy()
        fill.width = max(4, int(rect.width * ratio))
        pygame.draw.rect(surface, fill_color, fill, border_radius=3)
    text = font.render(label, True, COLOR_TEXT_DIM)
    surface.blit(text, (rect.x, rect.y - text.get_height() - 2))


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for ch in paragraph:
            trial = current + ch
            if font.size(trial)[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def blit_centered(
    surface: pygame.Surface,
    text_surf: pygame.Surface,
    center_x: int,
    y: int,
) -> None:
    rect = text_surf.get_rect(center=(center_x, y + text_surf.get_height() // 2))
    surface.blit(text_surf, rect)
