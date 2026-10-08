"""スコア登録用の画面上キーボード。"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

KEY_BS = "BS"
KEY_END = "戻"
KEY_SPACE = "□"

KEYBOARD_COLS = 13

KEYBOARD_ROWS: tuple[tuple[str, ...], ...] = (
    tuple("ABCDEFGHIJKLM"),
    tuple("NOPQRSTUVWXYZ"),
    tuple("abcdefghijklm"),
    tuple("nopqrstuvwxyz"),
    tuple("0123456789+-="),
    tuple(".,!?@:;[]()_/"),
    ("{", "}", "|", "~", "^", "#", "$", "%", "&", "*", KEY_SPACE, KEY_BS, KEY_END),
)

NAME_ENTRY_PANEL_FILL = (26, 88, 102, 215)
NAME_ENTRY_PANEL_BORDER = (90, 175, 195)
KEY_UNSELECTED = (228, 232, 240)
_JP_LABELS = frozenset({KEY_END, KEY_SPACE})


def _font_for_key_label(
    label: str,
    key_font: pygame.font.Font,
    jp_font: pygame.font.Font,
) -> pygame.font.Font:
    if label in _JP_LABELS or any(ord(ch) > 127 for ch in label):
        return jp_font
    return key_font


def _keyboard_cell_size(
    key_font: pygame.font.Font,
    jp_font: pygame.font.Font,
    L,
) -> tuple[int, int]:
    """フォントサイズはそのまま、セルは文字幅＋最小余白で詰める。"""
    max_w = 0
    max_h = key_font.get_height()
    for row in KEYBOARD_ROWS:
        for label in row:
            font = _font_for_key_label(label, key_font, jp_font)
            w, h = font.size(label)
            max_w = max(max_w, w)
            max_h = max(max_h, h)
    pad_x = max(2, L.x(1))
    pad_y = max(1, L.y(1))
    return max_w + pad_x, max_h + pad_y


def format_name_slots(name: str, max_len: int) -> str:
    """未入力はハイフンで埋める（アーケード風）。"""
    n = max(1, max_len)
    buf = (name or "")[:n]
    return buf + "-" * (n - len(buf))


def name_entry_panel_rect(container: pygame.Rect, L) -> pygame.Rect:
    margin_x = max(L.x(4), int(container.width * 0.02))
    margin_y = max(L.y(3), int(container.height * 0.02))
    return pygame.Rect(
        container.left + margin_x,
        container.top + margin_y,
        container.width - margin_x * 2,
        container.height - margin_y * 2,
    )


def draw_name_entry_panel(surface: pygame.Surface, panel: pygame.Rect) -> None:
    layer = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    layer.fill(NAME_ENTRY_PANEL_FILL)
    surface.blit(layer, panel.topleft)
    pygame.draw.rect(surface, NAME_ENTRY_PANEL_BORDER, panel, width=2)


def name_entry_keyboard_rect(panel: pygame.Rect, L) -> pygame.Rect:
    top = panel.top + int(panel.height * 0.28)
    bottom_pad = L.y(10)
    return pygame.Rect(
        panel.left + L.x(6),
        top,
        panel.width - L.x(12),
        panel.bottom - bottom_pad - top,
    )


@dataclass
class NameKeyboard:
    row: int = 0
    col: int = 0

    @property
    def rows(self) -> tuple[tuple[str, ...], ...]:
        return KEYBOARD_ROWS

    def selected_key(self) -> str:
        line = self.rows[self.row]
        return line[self.col]

    def move(self, dr: int, dc: int) -> None:
        if not self.rows:
            return
        r = self.row
        c = self.col
        if dr != 0:
            r = (r + dr) % len(self.rows)
            line = self.rows[r]
            c = min(c, len(line) - 1)
        if dc != 0:
            line = self.rows[r]
            c = (c + dc) % len(line)
        self.row = r
        self.col = c

    def apply_key(
        self,
        name: str,
        max_len: int,
    ) -> tuple[str, bool]:
        """キー決定。戻り値は (新しい名前, 登録完了したか)。"""
        key = self.selected_key()
        if key == KEY_END:
            return name, True
        if key == KEY_BS:
            return name[:-1], False
        if key == KEY_SPACE:
            if len(name) >= max_len:
                return name, False
            return name + " ", False
        if len(name) >= max_len:
            return name, False
        return name + key, False


def draw_name_keyboard(
    surface: pygame.Surface,
    *,
    keyboard: NameKeyboard,
    rect: pygame.Rect,
    key_font: pygame.font.Font,
    jp_font: pygame.font.Font,
    L,
) -> None:
    from kidgame.ui.draw_helpers import blit_centered_glow
    from kidgame.ui.theme import COLOR_CURSOR

    rows = keyboard.rows
    if not rows:
        return
    cols = KEYBOARD_COLS
    cell_w, cell_h = _keyboard_cell_size(key_font, jp_font, L)
    grid_w = cell_w * cols
    grid_h = cell_h * len(rows)
    start_x = rect.x + (rect.width - grid_w) // 2
    start_y = rect.y + (rect.height - grid_h) // 2

    for ri, line in enumerate(rows):
        row_w = cell_w * len(line)
        row_start_x = start_x + (grid_w - row_w) // 2
        for ci, label in enumerate(line):
            cx = row_start_x + ci * cell_w + cell_w // 2
            cy = start_y + ri * cell_h + cell_h // 2
            selected = ri == keyboard.row and ci == keyboard.col
            font = _font_for_key_label(label, key_font, jp_font)
            blit_centered_glow(
                surface,
                font,
                label,
                cx,
                cy,
                selected=selected,
                color=COLOR_CURSOR,
                dim_color=KEY_UNSELECTED,
            )
