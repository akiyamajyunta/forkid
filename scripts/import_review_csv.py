"""
難易度別 review CSV → questions.json（読込時に誤答を自動生成）

実行: python scripts/import_review_csv.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kidgame.data.loader import DATA_DIR
from kidgame.data.review_csv import load_question_bank_from_review_csvs

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "questions.json"


def main() -> None:
    bank = load_question_bank_from_review_csvs(DATA_DIR)
    payload = {
        "meta": {
            "source": "nazoq.com",
            "url": "https://nazoq.com/",
            "count": len(bank.questions),
            "review_csv_format": "correct_always_A_sparse_bcd",
            "license_note": "教育・私的利用向け。出典 nazoq.com を参照。",
        },
        "questions": [
            {
                "id": q.id,
                "levels": sorted(d.value for d in q.levels),
                "question": q.question,
                "options": list(q.options),
                "answer_index": 0,
                "hint": q.hint,
                **({"dev_explanation": q.dev_explanation} if q.dev_explanation else {}),
                **({"source": q.source} if q.source else {"source": "nazoq.com"}),
            }
            for q in bank.questions
        ],
    }
    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(bank.questions)} questions to {OUT_PATH}")


if __name__ == "__main__":
    main()
