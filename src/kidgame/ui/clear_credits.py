"""ゲームクリア（ライフ残り）時のクレジット文。"""

from __future__ import annotations

GAME_CLEAR_TITLE = "ゲームクリア"

# 表示順（空行は行間用）
CREDIT_LINES: tuple[str, ...] = (
    "— CREDITS —",
    "",
    "なぞなぞ大作戦",
    "",
    "Program",
    "  kidgame",
    "",
    "なぞなぞデータ",
    "  なぞなぞ問題いっぱい",
    "  nazonazo.nihonsimondai.com",
    "",
    "Python / pygame-ce",
)
