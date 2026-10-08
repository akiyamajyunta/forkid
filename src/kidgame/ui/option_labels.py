"""画面上の選択肢ラベル（上から A, B, C…）。データ上の answer_index とは別。"""

from __future__ import annotations


def option_display_letter(display_slot: int) -> str:
    if display_slot < 0 or display_slot > 25:
        return "?"
    return chr(ord("A") + display_slot)
