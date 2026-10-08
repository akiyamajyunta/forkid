from __future__ import annotations

from pathlib import Path

from kidgame.data.models import Difficulty
from kidgame.system import score_store as mod
from kidgame.system.leaderboard import (
    LeaderboardEntry,
    format_score,
    insert_entry,
    padded_entries,
    placeholder_entry,
    preview_after_insert,
    row_display,
)


def test_preview_finds_insert_rank() -> None:
    entries = [
        LeaderboardEntry("a", 100, played_at="2026/01/01 12:00", accuracy=50.0),
        LeaderboardEntry("b", 50, played_at="2026/01/02 12:00", accuracy=40.0),
    ]
    merged, rank = preview_after_insert(
        entries,
        name="-",
        score=75,
        played_at="2026/04/08 21:00",
        accuracy=80.0,
    )
    assert len(merged) == 3
    assert rank == 2
    assert merged[1].score == 75


def test_insert_keeps_top_ten() -> None:
    entries = [
        LeaderboardEntry("a", 100, played_at="2026/01/01 12:00", accuracy=50.0)
    ]
    for i in range(12):
        entries = insert_entry(
            entries,
            f"p{i}",
            i * 10,
            played_at="2026/01/02 12:00",
            accuracy=10.0,
        )
    assert len(entries) == 10
    assert entries[0].score == 110


def test_padded_uses_hyphen() -> None:
    rows = padded_entries([LeaderboardEntry("x", 1, "2026/01/01 10:00", 80.0)])
    assert len(rows) == 10
    name, score, date, acc = row_display(rows[1])
    assert name == "-"
    assert score == format_score(0)
    assert acc == "0.0%"


def test_add_leaderboard_persists(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "SCORES_PATH", tmp_path / "scores.json")
    store = mod.ScoreStore.empty()
    store.add_leaderboard_entry(
        Difficulty.EASY,
        "テスト",
        999,
        played_at="2026/04/08 21:00",
        accuracy=66.7,
    )
    store2 = mod.ScoreStore.load()
    board = store2.leaderboard(Difficulty.EASY)
    assert len(board) == 1
    assert board[0].name == "テスト"
    assert board[0].score == 999
    assert board[0].played_at == "2026/04/08 21:00"
    assert board[0].accuracy == 66.7
