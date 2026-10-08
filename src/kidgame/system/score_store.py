"""最高得点の永続化（~/.kidgame/scores.json）。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from kidgame.data.models import Difficulty
from kidgame.ui.display_config import CONFIG_DIR

SCORES_PATH = CONFIG_DIR / "scores.json"


@dataclass
class ScoreStore:
    high_by_difficulty: dict[str, int]

    @classmethod
    def empty(cls) -> ScoreStore:
        return cls(high_by_difficulty={d.value: 0 for d in Difficulty})

    @classmethod
    def load(cls) -> ScoreStore:
        if not SCORES_PATH.is_file():
            return cls.empty()
        try:
            data = json.loads(SCORES_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls.empty()
        raw = data.get("high_by_difficulty", {})
        store = cls.empty()
        if isinstance(raw, dict):
            for key in store.high_by_difficulty:
                if key in raw:
                    store.high_by_difficulty[key] = max(0, int(raw[key]))
        return store

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        SCORES_PATH.write_text(
            json.dumps({"high_by_difficulty": self.high_by_difficulty}, ensure_ascii=False, indent=2),
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
