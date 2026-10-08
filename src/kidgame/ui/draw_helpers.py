from __future__ import annotations

import math

import pygame

from kidgame.ui.theme import (
    COLOR_BAND_RED,
    COLOR_BAND_RED_ALPHA,
    COLOR_BORDER_DARK,
    COLOR_BORDER_GOLD,
    COLOR_CONTAINER_FILL,
    COLOR_CONTAINER_INNER,
    COLOR_CURSOR,
    COLOR_GAUGE_BG,
    COLOR_MAIN_PANEL,
    COLOR_MAIN_PANEL_INNER,
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


def _blit_alpha_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    rgba: tuple[int, int, int, int],
) -> None:
    layer = pygame.Surface((max(1, rect.width), max(1, rect.height)), pygame.SRCALPHA)
    layer.fill(rgba)
    surface.blit(layer, rect.topleft)


def draw_wagara_frame(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, COLOR_BORDER_DARK, rect, width=3, border_radius=8)
    inner = rect.inflate(-6, -6)
    pygame.draw.rect(surface, COLOR_BORDER_GOLD, inner, width=2, border_radius=6)


def draw_game_container(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """問題＋選択肢を包む外枠（赤枠サイズ相当）。"""
    _blit_alpha_rect(surface, rect, COLOR_CONTAINER_FILL)
    draw_wagara_frame(surface, rect)


def draw_game_section(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """外枠内の問題文／選択肢用サブウィンドウ。"""
    _blit_alpha_rect(surface, rect, COLOR_CONTAINER_INNER)
    pygame.draw.rect(surface, COLOR_BORDER_GOLD, rect, width=2, border_radius=5)
    pygame.draw.rect(surface, COLOR_BORDER_DARK, rect.inflate(-3, -3), width=1, border_radius=4)


def draw_background_red_band(
    surface: pygame.Surface,
    width: int,
    height: int,
    *,
    top_ratio: float = 0.52,
    height_ratio: float = 0.34,
) -> None:
    """和柄の上に重ねる半透明の赤い横帯（旧オーバーレイの茶帯の代わり）。"""
    band_top = int(height * top_ratio)
    band_h = max(1, int(height * height_ratio))
    layer = pygame.Surface((width, band_h), pygame.SRCALPHA)
    layer.fill((*COLOR_BAND_RED, COLOR_BAND_RED_ALPHA))
    surface.blit(layer, (0, band_top))


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, *, status: bool = False) -> None:
    if status:
        _blit_alpha_rect(
            surface,
            rect,
            (COLOR_STATUS_PANEL[0], COLOR_STATUS_PANEL[1], COLOR_STATUS_PANEL[2], 190),
        )
    else:
        _blit_alpha_rect(
            surface,
            rect,
            (
                COLOR_MAIN_PANEL[0],
                COLOR_MAIN_PANEL[1],
                COLOR_MAIN_PANEL[2],
                185,
            ),
        )
    draw_wagara_frame(surface, rect)


def layout_option_row(
    bar: pygame.Rect,
    label_surf: pygame.Surface,
    main_font: pygame.font.Font,
    ruby_font: pygame.font.Font,
    *,
    has_ruby: bool,
    pad_x: int,
) -> tuple[int, int, int]:
    """選択肢バー内のルビ付き本文と「A.」ラベルの縦位置を揃える。"""
    main_h = main_font.get_height()
    from kidgame.ui.ruby_draw import RUBY_MAIN_GAP

    ruby_band = ruby_font.get_height() + RUBY_MAIN_GAP if has_ruby else 0
    block_h = ruby_band + main_h
    block_top = bar.centery - block_h // 2
    main_row_top = block_top + ruby_band
    label_x = bar.x + pad_x
    label_y = main_row_top
    text_y = block_top
    return text_y, label_x, label_y


def draw_option_bar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    selected: bool = False,
    tile: pygame.Surface | None = None,
) -> None:
    """選択肢用の横長ブロック（ワイヤーフレームの選択肢バー）。"""
    if tile is not None:
        stretched = pygame.transform.smoothscale(
            tile, (max(1, rect.width), max(1, rect.height))
        )
        surface.blit(stretched, rect.topleft)
        if selected:
            pygame.draw.rect(surface, COLOR_CURSOR, rect, width=3, border_radius=5)
        return
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


def render_outlined(
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    outline: tuple[int, int, int] = (0, 0, 0),
    outline_width: int = 2,
) -> pygame.Surface:
    base = font.render(text, True, color)
    w, h = base.get_size()
    pad = outline_width * 2
    canvas = pygame.Surface((w + pad, h + pad), pygame.SRCALPHA)
    ox, oy = outline_width, outline_width
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            shadow = font.render(text, True, outline)
            canvas.blit(shadow, (ox + dx, oy + dy))
    canvas.blit(base, (ox, oy))
    return canvas


def blit_outlined(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    surface.blit(render_outlined(font, text, color), (x, y))


def blit_centered_outlined(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center_x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    surf = render_outlined(font, text, color)
    rect = surf.get_rect(midtop=(center_x, y))
    surface.blit(surf, rect)


def draw_star_row(
    surface: pygame.Surface,
    x: int,
    y: int,
    *,
    filled: int,
    total: int,
    size: int,
) -> None:
    gap = max(4, size // 3)
    for i in range(total):
        cx = x + i * (size + gap) + size // 2
        cy = y + size // 2
        if i < filled:
            _draw_star(surface, cx, cy, size // 2, (70, 130, 220), (0, 0, 0))
        else:
            _draw_star(surface, cx, cy, size // 2, (40, 48, 60), (0, 0, 0), hollow=True)


def _draw_star(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    r: int,
    fill: tuple[int, int, int],
    border: tuple[int, int, int],
    *,
    hollow: bool = False,
) -> None:
    points: list[tuple[int, int]] = []
    for i in range(10):
        ang = -90 + i * 36
        rad = r if i % 2 == 0 else r // 2
        px = cx + int(math.cos(math.radians(ang)) * rad)
        py = cy + int(math.sin(math.radians(ang)) * rad)
        points.append((px, py))
    if hollow:
        pygame.draw.polygon(surface, border, points, width=2)
    else:
        pygame.draw.polygon(surface, fill, points)
        pygame.draw.polygon(surface, border, points, width=1)


def scale_cover(surface: pygame.Surface, width: int, height: int) -> pygame.Surface:
    """画面全体を覆うように拡大（はみ出しは中央トリム）。"""
    sw, sh = surface.get_size()
    if sw <= 0 or sh <= 0:
        return surface
    scale = max(width / sw, height / sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    scaled = pygame.transform.smoothscale(surface, (nw, nh))
    if nw == width and nh == height:
        return scaled
    x = (nw - width) // 2
    y = (nh - height) // 2
    cropped = pygame.Surface((width, height))
    cropped.blit(scaled, (0, 0), pygame.Rect(x, y, width, height))
    return cropped
