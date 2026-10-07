"""
questions.json → 確認用 CSV（Excel 向け UTF-8 BOM）

実行: python scripts/export_review_csv.py
出力: data/questions_review.csv
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "questions.json"
OUT_PATH = ROOT / "data" / "questions_review.csv"

HEADERS = [
    "ID",
    "出典No",
    "出題レベル",
    "問題文",
    "選択肢A",
    "選択肢B",
    "選択肢C",
    "選択肢D",
    "選択肢E",
    "選択肢F",
    "正解記号",
    "正解テキスト",
    "ヒント",
    "開発者解説",
]


def _levels_label(raw: dict) -> str:
    if "levels" in raw:
        return " / ".join(raw["levels"])
    return str(raw.get("difficulty", ""))


def _answer_symbol(index: int) -> str:
    return chr(ord("A") + index)


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    questions = data["questions"]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        for q in questions:
            opts = q["options"]
            while len(opts) < 6:
                opts = [*opts, ""]
            ans_i = int(q["answer_index"])
            writer.writerow(
                [
                    q.get("id", ""),
                    q.get("source_no", ""),
                    _levels_label(q),
                    q.get("question", ""),
                    opts[0],
                    opts[1],
                    opts[2],
                    opts[3],
                    opts[4],
                    opts[5],
                    _answer_symbol(ans_i),
                    opts[ans_i],
                    q.get("hint", ""),
                    q.get("dev_explanation", "").replace("\n", " / "),
                ]
            )

    print(f"Wrote {len(questions)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
