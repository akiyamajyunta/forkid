from __future__ import annotations

import csv
from pathlib import Path

from kidgame.data.models import Difficulty
from kidgame.data.review_csv import (
    REVIEW_CSV_HEADERS,
    load_question_bank_from_review_csvs,
    question_dict_from_review_row,
    review_csv_path,
)


def test_sparse_bc_expands_options(tmp_path: Path) -> None:
    row_map = {
        "ID": "q1",
        "問題文": "なぞ?",
        "選択肢A": "正答",
        "選択肢B": "",
        "選択肢C": "",
        "選択肢D": "",
        "正解記号": "A",
        "正解テキスト": "正答",
        "ヒント": "ヒント",
        "開発者解説": "",
    }
    raw = question_dict_from_review_row(row_map, Difficulty.EASY, ["正答", "りんご"])
    assert raw["options"][0] == "正答"
    assert raw["answer_index"] == 0
    assert len([o for o in raw["options"] if o]) >= 3


def test_four_option_row_loads_from_csv(tmp_path: Path) -> None:
    row = ["q1", "なぞ?", "正答", "b", "c", "d", "A", "正答", "ヒント", ""]
    for diff in Difficulty:
        path = review_csv_path(tmp_path, diff)
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(REVIEW_CSV_HEADERS)
            w.writerow(row)
    bank = load_question_bank_from_review_csvs(tmp_path)
    q = bank.questions[0]
    assert q.options[0] == "正答"
    assert q.answer_index == 0
    assert len([o for o in q.options if o]) >= 3
