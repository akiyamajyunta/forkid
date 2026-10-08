"""難易度別ベスト10（名前・得点・日時・正答率）。"""

from __future__ import annotations

from dataclasses import dataclass

from kidgame.data.models import Difficulty

LEADERBOARD_SIZE = 10
PLACEHOLDER_NAME = "-"
EMPTY_DATE = "----/--/-- --:--"
SCORE_PAD_WIDTH = 8


@dataclass(frozen=True, slots=True)
class LeaderboardEntry:
    name: str
    score: int
    played_at: str = ""
    accuracy: float = 0.0

    @classmethod
    def from_dict(cls, raw: object) -> LeaderboardEntry | None:
        if not isinstance(raw, dict):
            return None
        name = str(raw.get("name", "")).strip()
        try:
            score = int(raw.get("score", 0))
        except (TypeError, ValueError):
            return None
        played_at = str(raw.get("played_at", "")).strip()
        try:
            accuracy = float(raw.get("accuracy", 0.0))
        except (TypeError, ValueError):
            accuracy = 0.0
        return cls(
            name=name,
            score=max(0, score),
            played_at=played_at,
            accuracy=max(0.0, min(100.0, accuracy)),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "score": self.score,
            "played_at": self.played_at,
            "accuracy": round(self.accuracy, 1),
        }


def empty_leaderboards() -> dict[str, list[LeaderboardEntry]]:
    return {d.value: [] for d in Difficulty}


def placeholder_entry() -> LeaderboardEntry:
    return LeaderboardEntry(
        name=PLACEHOLDER_NAME,
        score=0,
        played_at="",
        accuracy=0.0,
    )


def is_placeholder(entry: LeaderboardEntry) -> bool:
    return (
        entry.name == PLACEHOLDER_NAME
        and entry.score == 0
        and not entry.played_at
    )


def format_score(score: int) -> str:
    return f"{max(0, score):0{SCORE_PAD_WIDTH}d}"


def format_accuracy(accuracy: float) -> str:
    return f"{max(0.0, min(100.0, accuracy)):.1f}%"


def row_display(entry: LeaderboardEntry) -> tuple[str, str, str, str]:
    if is_placeholder(entry):
        return (
            PLACEHOLDER_NAME,
            format_score(0),
            EMPTY_DATE,
            format_accuracy(0.0),
        )
    date = entry.played_at if entry.played_at else EMPTY_DATE
    return (
        entry.name,
        format_score(entry.score),
        date,
        format_accuracy(entry.accuracy),
    )


def padded_entries(entries: list[LeaderboardEntry]) -> list[LeaderboardEntry]:
    out = list(entries[:LEADERBOARD_SIZE])
    while len(out) < LEADERBOARD_SIZE:
        out.append(placeholder_entry())
    return out


def preview_after_insert(
    entries: list[LeaderboardEntry],
    *,
    name: str,
    score: int,
    played_at: str,
    accuracy: float,
) -> tuple[list[LeaderboardEntry], int]:
    """挿入後の上位10件と、挿入行の順位（1始まり）。"""
    clean = (name or "").strip()
    merged = insert_entry(
        entries,
        clean,
        score,
        played_at=played_at,
        accuracy=accuracy,
    )
    for i, entry in enumerate(merged, start=1):
        if (
            entry.name == clean
            and entry.score == max(0, score)
            and entry.played_at == played_at
        ):
            return merged, i
    return merged, min(len(merged), LEADERBOARD_SIZE)


def insert_entry(
    entries: list[LeaderboardEntry],
    name: str,
    score: int,
    *,
    played_at: str,
    accuracy: float,
) -> list[LeaderboardEntry]:
    clean = (name or "").strip()
    merged = list(entries) + [
        LeaderboardEntry(
            name=clean,
            score=max(0, score),
            played_at=played_at,
            accuracy=max(0.0, min(100.0, accuracy)),
        )
    ]
    merged.sort(key=lambda e: e.score, reverse=True)
    return merged[:LEADERBOARD_SIZE]
