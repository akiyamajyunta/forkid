from __future__ import annotations

import pygame

from kidgame.ui.draw_helpers import layout_option_row


def test_option_label_aligns_with_main_row() -> None:
    pygame.font.init()
    main = pygame.font.SysFont(None, 28)
    ruby = pygame.font.SysFont(None, 14)
    label = main.render("A.", True, (255, 255, 255))
    bar = pygame.Rect(0, 0, 400, 48)
    text_y, _lx, label_y = layout_option_row(
        bar, label, main, ruby, has_ruby=True, pad_x=10
    )
    ruby_band = ruby.get_height() + 1
    main_row_top = text_y + ruby_band
    assert label_y == main_row_top
