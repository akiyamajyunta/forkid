from __future__ import annotations

import csv
from pathlib import Path

import pytest

from kidgame.data.loader import load_questions_bank
from kidgame.data.models import Difficulty
from kidgame.data.review_csv import (
    REVIEW_CSV_HEADERS,
    load_question_bank_from_review_csvs,
    options_from_review_row,
    review_csv_path,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_options_from_review_row_keeps_abcd_columns() -> None:
    row = {
        "ID": "t",
        "選択肢A": "はし",
        "選択肢B": "b",
        "選択肢C": "c",
        "選択肢D": "d",
        "正解記号": "A",
        "正解テキスト": "箸（はし）",
    }
    opts, ai = options_from_review_row(row)
    assert ai == 0
    assert opts[0] == "はし"
    assert opts[1] == "b"


def test_load_real_easy_review_csv() -> None:
    bank = load_question_bank_from_review_csvs(DATA_DIR)
    assert len(bank.questions) >= 100


def test_review_csv_files_exist() -> None:
    for d in Difficulty:
        assert review_csv_path(DATA_DIR, d).is_file()


def test_load_bank_from_review_csvs_matches_json_pool_sizes() -> None:
    import json

    from kidgame.data.loader import load_questions_file

    meta = json.loads((DATA_DIR / "questions.json").read_text(encoding="utf-8")).get(
        "meta", {}
    )
    if meta.get("imported_from") == "build_questions_from_nazoq.py":
        pytest.skip("questions.json は nazoq 取込後、CSV と件数が一致する想定")

    csv_bank = load_question_bank_from_review_csvs(DATA_DIR)
    json_bank = load_questions_file(DATA_DIR / "questions.json")
    assert len(csv_bank.questions) == len(json_bank.questions)
    for mode in Difficulty:
        assert len(csv_bank.for_mode(mode)) == len(json_bank.for_mode(mode))


def test_default_loader_prefers_review_csvs() -> None:
    bank = load_questions_bank()
    assert len(bank.for_mode(Difficulty.EASY)) >= 10


def test_merged_levels_for_shared_question(tmp_path: Path) -> None:
    row = ["q1", "テスト?", "a", "b", "c", "d", "A", "a", "hint", ""]
    for mode in Difficulty:
        path = review_csv_path(tmp_path, mode)
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(REVIEW_CSV_HEADERS)
            w.writerow(row)
    bank = load_question_bank_from_review_csvs(tmp_path)
    assert len(bank.questions) == 1
    assert bank.questions[0].levels == frozenset(Difficulty)


def test_legacy_csv_headers_without_d_column(tmp_path: Path) -> None:
    legacy_row = ["q1", "テスト?", "a", "b", "c", "A", "a", "hint", ""]
    for mode in Difficulty:
        path = review_csv_path(tmp_path, mode)
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "ID",
                    "問題文",
                    "選択肢A",
                    "選択肢B",
                    "選択肢C",
                    "正解記号",
                    "正解テキスト",
                    "ヒント",
                    "開発者解説",
                ]
            )
            w.writerow(legacy_row)
    bank = load_question_bank_from_review_csvs(tmp_path)
    assert bank.questions[0].options[0] == "a"


def test_divergent_same_id_keeps_first_body_merges_levels(tmp_path: Path) -> None:
    base = ["q1", "テスト?", "a", "b", "c", "d", "A", "a", "hint", ""]
    easy_path = review_csv_path(tmp_path, Difficulty.EASY)
    with easy_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(REVIEW_CSV_HEADERS)
        w.writerow(base)
    normal_row = list(base)
    normal_row[1] = "別の問題?"
    normal_path = review_csv_path(tmp_path, Difficulty.NORMAL)
    with normal_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(REVIEW_CSV_HEADERS)
        w.writerow(normal_row)
    hard_path = review_csv_path(tmp_path, Difficulty.HARD)
    with hard_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(REVIEW_CSV_HEADERS)
        w.writerow(base)

    bank = load_question_bank_from_review_csvs(tmp_path)
    assert len(bank.questions) == 1
    assert bank.questions[0].question == "テスト?"
    assert bank.questions[0].levels == frozenset(Difficulty)
