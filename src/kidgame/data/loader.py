from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from kidgame.data.models import Difficulty, Question, QuestionBank
from kidgame.data.review_csv import (
    all_review_csvs_present,
    load_question_bank_from_review_csvs,
)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DEFAULT_QUESTIONS_PATH = DATA_DIR / "questions.json"


def load_questions_file(path: Path | str) -> QuestionBank:
    """単一 JSON ファイルから問題バンクを読み込む。"""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Questions file not found: {file_path}")

    with file_path.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    return QuestionBank.from_dict(data)


def load_questions_bank(
    path: Path | str | None = None,
    *,
    data_dir: Path | str | None = None,
) -> QuestionBank:
    """
    問題バンクを読み込む。
    path 未指定時: data 内の難易度別 review CSV が揃っていればそちらを優先、なければ questions.json。
    """
    if path is not None:
        return load_questions_file(path)

    base = Path(data_dir) if data_dir is not None else DATA_DIR
    if all_review_csvs_present(base):
        return load_question_bank_from_review_csvs(base)
    return load_questions_file(base / "questions.json")


class QuestionRepository:
    """
    難易度別の問題プール管理。
    ゲーム開始時にシャッフルし、指定数だけ取り出す。
    """

    def __init__(self, bank: QuestionBank) -> None:
        self._bank = bank
        self._pools: dict[Difficulty, list[Question]] = {
            d: list(bank.for_mode(d)) for d in Difficulty
        }

    @classmethod
    def from_file(
        cls,
        path: Path | str | None = None,
        *,
        data_dir: Path | str | None = None,
    ) -> QuestionRepository:
        return cls(load_questions_bank(path, data_dir=data_dir))

    def available_count(self, difficulty: Difficulty) -> int:
        return len(self._pools[difficulty])

    def reset_pool(self, difficulty: Difficulty) -> None:
        self._pools[difficulty] = list(self._bank.for_mode(difficulty))

    def shuffle_pool(self, difficulty: Difficulty, *, rng: random.Random | None = None) -> None:
        r = rng if rng is not None else random
        r.shuffle(self._pools[difficulty])

    def draw(
        self,
        difficulty: Difficulty,
        count: int,
        *,
        shuffle: bool = True,
        rng: random.Random | None = None,
    ) -> list[Question]:
        """
        難易度に合う問題を count 件返す。
        プール不足時は ValueError。返却後、取り出した問題はプールから除く。
        """
        if count < 0:
            raise ValueError("count must be non-negative")

        pool = self._pools[difficulty]
        if len(pool) < count:
            raise ValueError(
                f"Not enough {difficulty.value} questions: need {count}, have {len(pool)}"
            )

        if shuffle:
            self.shuffle_pool(difficulty, rng=rng)

        drawn = pool[:count]
        del pool[:count]
        return drawn

    def peek_all(self, difficulty: Difficulty) -> tuple[Question, ...]:
        """シャッフルせず現在プールのスナップショット（デバッグ・テスト用）。"""
        return tuple(self._pools[difficulty])
