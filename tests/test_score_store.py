from __future__ import annotations

from pathlib import Path

from kidgame.data.models import Difficulty
from kidgame.system import score_store as mod


def test_record_session_updates_high_score(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "SCORES_PATH", tmp_path / "scores.json")
    store = mod.ScoreStore.empty()
    assert store.record_session(Difficulty.EASY, 500) == 500
    store2 = mod.ScoreStore.load()
    assert store2.high_score(Difficulty.EASY) == 500
    assert store2.record_session(Difficulty.EASY, 300) == 500
    assert store2.record_session(Difficulty.EASY, 800) == 800
