"""最高得点・ランキングの永続化（~/.kidgame/scores.json）。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from kidgame.data.models import Difficulty
from kidgame.system.leaderboard import (
    LeaderboardEntry,
    empty_leaderboards,
    insert_entry,
    padded_entries,
)
SCORES_PATH = Path.home() / ".kidgame" / "scores.json"


@dataclass
class ScoreStore:
    high_by_difficulty: dict[str, int]
    leaderboards: dict[str, list[LeaderboardEntry]] = field(
        default_factory=empty_leaderboards
    )

    @classmethod
    def empty(cls) -> ScoreStore:
        return cls(
            high_by_difficulty={d.value: 0 for d in Difficulty},
            leaderboards=empty_leaderboards(),
        )

    @classmethod
    def load(cls) -> ScoreStore:
        if not SCORES_PATH.is_file():
            return cls.empty()
        try:
            data = json.loads(SCORES_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls.empty()
        store = cls.empty()
        raw_high = data.get("high_by_difficulty", {})
        if isinstance(raw_high, dict):
            for key in store.high_by_difficulty:
                if key in raw_high:
                    store.high_by_difficulty[key] = max(0, int(raw_high[key]))
        raw_boards = data.get("leaderboards", {})
        if isinstance(raw_boards, dict):
            for key in store.leaderboards:
                items = raw_boards.get(key, [])
                if not isinstance(items, list):
                    continue
                parsed: list[LeaderboardEntry] = []
                for item in items:
                    entry = LeaderboardEntry.from_dict(item)
                    if entry is not None:
                        parsed.append(entry)
                store.leaderboards[key] = parsed
        return store

    def save(self) -> None:
        SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "high_by_difficulty": self.high_by_difficulty,
            "leaderboards": {
                key: [e.to_dict() for e in entries]
                for key, entries in self.leaderboards.items()
            },
        }
        SCORES_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def high_score(self, difficulty: Difficulty) -> int:
        return self.high_by_difficulty.get(difficulty.value, 0)

    def record_session(self, difficulty: Difficulty, session_score: int) -> int:
        key = difficulty.value
        prev = self.high_by_difficulty.get(key, 0)
        new_high = max(prev, session_score)
        if new_high != prev:
            self.high_by_difficulty[key] = new_high
            self.save()
        return new_high

    def leaderboard(self, difficulty: Difficulty) -> list[LeaderboardEntry]:
        return list(self.leaderboards.get(difficulty.value, []))

    def leaderboard_padded(self, difficulty: Difficulty) -> list[LeaderboardEntry]:
        return padded_entries(self.leaderboard(difficulty))

    def add_leaderboard_entry(
        self,
        difficulty: Difficulty,
        name: str,
        score: int,
        *,
        played_at: str,
        accuracy: float,
    ) -> None:
        key = difficulty.value
        current = self.leaderboards.get(key, [])
        self.leaderboards[key] = insert_entry(
            current,
            name,
            score,
            played_at=played_at,
            accuracy=accuracy,
        )
        self.save()
