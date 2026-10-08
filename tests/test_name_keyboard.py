from __future__ import annotations

from kidgame.ui.name_keyboard import NameKeyboard, format_name_slots


def test_format_name_slots_pads_hyphen() -> None:
    assert format_name_slots("ab", 5) == "ab---"


def test_keyboard_backspace_and_end() -> None:
    kb = NameKeyboard()
    bs_row = next(i for i, row in enumerate(kb.rows) if "BS" in row)
    kb.row = bs_row
    kb.col = kb.rows[bs_row].index("BS")
    name, done = kb.apply_key("abc", 12)
    assert name == "ab" and not done
    end_row = next(i for i, row in enumerate(kb.rows) if "戻" in row)
    kb.row = end_row
    kb.col = kb.rows[end_row].index("戻")
    name, done = kb.apply_key("ab", 12)
    assert done

