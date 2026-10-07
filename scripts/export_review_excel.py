"""
questions.json → 確認用 Excel（.xlsx）

実行: python scripts/export_review_excel.py
出力: data/questions_review.xlsx
"""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "questions.json"
OUT_PATH = ROOT / "data" / "questions_review.xlsx"

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
    "正解",
    "正解テキスト",
    "ヒント",
    "開発者解説",
]

# 列番号 1-based: 正解記号=11, 選択肢A=5 ... F=10
OPT_COL_START = 5
OPT_COL_END = 10
ANS_SYM_COL = 11
ANS_TEXT_COL = 12


def _levels_label(raw: dict) -> str:
    if "levels" in raw:
        return " / ".join(raw["levels"])
    return str(raw.get("difficulty", ""))


def _build_rows(data: dict) -> list[list]:
    rows: list[list] = []
    for q in data["questions"]:
        opts = list(q["options"])
        while len(opts) < 6:
            opts.append("")
        ans_i = int(q["answer_index"])
        rows.append(
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
                chr(ord("A") + ans_i),
                opts[ans_i],
                q.get("hint", ""),
                q.get("dev_explanation", "").replace("\n", "\n"),
            ]
        )
    return rows


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    rows = _build_rows(data)

    wb = Workbook()
    ws = wb.active
    ws.title = "なぞなぞ一覧"

    header_fill = PatternFill("solid", fgColor="2F4F6F")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    correct_fill = PatternFill("solid", fgColor="C6EFCE")
    correct_opt_fill = PatternFill("solid", fgColor="E2F0D9")
    wrap = Alignment(wrap_text=True, vertical="top")
    thin = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    ws.append(HEADERS)
    for col in range(1, len(HEADERS) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border

    for q_idx, q in enumerate(data["questions"]):
        row_data = rows[q_idx]
        ws.append(row_data)
        excel_row = q_idx + 2
        ans_i = int(q["answer_index"])
        correct_col = OPT_COL_START + ans_i

        for col in range(1, len(HEADERS) + 1):
            cell = ws.cell(row=excel_row, column=col)
            cell.alignment = wrap
            cell.border = border
            if col in (ANS_SYM_COL, ANS_TEXT_COL):
                cell.fill = correct_fill
                cell.font = Font(bold=True)
            if col == correct_col:
                cell.fill = correct_opt_fill
                cell.font = Font(bold=True)

    widths = {
        1: 12,
        2: 8,
        3: 16,
        4: 48,
        5: 18,
        6: 18,
        7: 18,
        8: 18,
        9: 18,
        10: 18,
        11: 6,
        12: 20,
        13: 36,
        14: 52,
    }
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}{len(rows) + 1}"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_PATH)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
