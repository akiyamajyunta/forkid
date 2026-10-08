"""
questions.json → 難易度別確認用 CSV（Excel 向け UTF-8 BOM）

実行: python scripts/export_review_csv.py
出力:
  data/questions_review_easy.csv
  data/questions_review_normal.csv
  data/questions_review_hard.csv
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from kidgame.data.models import Difficulty
from kidgame.data.review_csv import (
    REVIEW_CSV_HEADERS,
    question_in_mode,
    question_to_review_row,
    review_csv_path,
)

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "questions.json"


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    questions = data["questions"]
    out_dir = ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    for mode in Difficulty:
        path = review_csv_path(out_dir, mode)
        rows = [q for q in questions if question_in_mode(q, mode)]
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(REVIEW_CSV_HEADERS)
            for q in rows:
                writer.writerow(question_to_review_row(q))
        print(f"Wrote {len(rows)} rows to {path}")


if __name__ == "__main__":
    main()
