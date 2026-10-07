from __future__ import annotations

import pygame

from kidgame.data.furigana import RubySegment, segments_or_reading_line
from kidgame.ui.draw_helpers import wrap_text

# Excel の「ルビ」表示に近い、ルビ直下の漢字との縦間隔（px）
RUBY_MAIN_GAP = 1
# セグメント間の横間隔（px）
RUBY_SEGMENT_PAD = 2


def draw_ruby_segments(
    surface: pygame.Surface,
    segments: tuple[RubySegment, ...],
    x: int,
    y: int,
    max_width: int,
    main_font: pygame.font.Font,
    ruby_font: pygame.font.Font,
    color: tuple[int, int, int],
    ruby_color: tuple[int, int, int],
) -> int:
    cx = x
    cy = y
    main_h = main_font.get_height()
    has_any_ruby = any(s.reading for s in segments)
    ruby_band_h = ruby_font.get_height() if has_any_ruby else 0
    main_row_y_offset = ruby_band_h + RUBY_MAIN_GAP if has_any_ruby else 0
    row_h = main_row_y_offset + main_h + 2

    for seg in segments:
        if not seg.text:
            continue
        main_surf = main_font.render(seg.text, True, color)
        main_w = main_surf.get_width()
        ruby_w = 0
        ruby_surf = None
        if seg.reading:
            ruby_surf = ruby_font.render(seg.reading, True, ruby_color)
            ruby_w = ruby_surf.get_width()
        seg_w = max(main_w, ruby_w)
        if cx + seg_w > x + max_width and cx > x:
            cx = x
            cy += row_h
        ty = cy + main_row_y_offset
        if ruby_surf is not None:
            rx = cx + max(0, (seg_w - ruby_w) // 2)
            surface.blit(ruby_surf, (rx, cy))
        surface.blit(main_surf, (cx, ty))
        cx += seg_w + RUBY_SEGMENT_PAD

    return cy + row_h


def draw_text_with_furigana(
    surface: pygame.Surface,
    text: str,
    ruby: tuple[RubySegment, ...] | None,
    x: int,
    y: int,
    max_width: int,
    main_font: pygame.font.Font,
    ruby_font: pygame.font.Font,
    furigana_font: pygame.font.Font,
    color: tuple[int, int, int],
    ruby_color: tuple[int, int, int],
    reading_color: tuple[int, int, int],
) -> int:
    segments, reading_line = segments_or_reading_line(text, ruby)
    if segments:
        return draw_ruby_segments(
            surface,
            segments,
            x,
            y,
            max_width,
            main_font,
            ruby_font,
            color,
            ruby_color,
        )

    for line in wrap_text(text, main_font, max_width):
        surf = main_font.render(line, True, color)
        surface.blit(surf, (x, y))
        y += surf.get_height() + 2

    if reading_line:
        for line in wrap_text(reading_line, furigana_font, max_width):
            surf = furigana_font.render(line, True, reading_color)
            surface.blit(surf, (x + 8, y))
            y += surf.get_height() + 1
        y += 4
    return y
