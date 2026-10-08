"""
review CSV の B/C は空欄のまま。questions.json だけ誤答を再生成する。

実行: python scripts/regenerate_review_options.py
      python scripts/import_review_csv.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kidgame.data.loader import DATA_DIR
from kidgame.data.review_csv import load_question_bank_from_review_csvs

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    bank = load_question_bank_from_review_csvs(DATA_DIR)
    print(f"Loaded {len(bank.questions)} questions (options expanded for play)")
    print("Run: python scripts/import_review_csv.py")


if __name__ == "__main__":
    main()
