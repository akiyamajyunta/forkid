"""
review 形式の CSV / Excel から、空欄の選択肢 B〜D を自動生成して CSV 出力する。

  python scripts/fill_review_csv_distractors.py ^
    --input "C:\\Users\\...\\easy.xlsx" ^
    --output "C:\\Users\\...\\easy_completed.csv"
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kidgame.data.distractors import (
    _score_candidate,
    answer_looks_like_food,
    build_six_options,
    extract_dai_keyword,
    food_mode_heuristic,
    question_wants_food_distractors,
)
from kidgame.data.kid_language import is_kid_friendly_distractor
from kidgame.data.review_csv import (
    CORRECT_ANSWER_SYMBOL,
    REVIEW_CSV_HEADERS,
    _stable_rng,
    normalize_review_csv_headers,
)

def _read_rows(path: Path) -> list[dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
            canonical = normalize_review_csv_headers(list(headers))
            if canonical is None:
                raise ValueError(f"Unexpected headers in {path}")
            rows: list[dict[str, str]] = []
            for row in reader:
                if not row or not any(cell.strip() for cell in row):
                    continue
                padded = row + [""] * (len(canonical) - len(row))
                rows.append({h: padded[i].strip() for i, h in enumerate(canonical)})
            return rows

    if suffix in {".xlsx", ".xlsm"}:
        try:
            import openpyxl
        except ImportError as e:
            raise SystemExit(
                "openpyxl が必要です: python -m pip install openpyxl"
            ) from e
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        raw = list(ws.iter_rows(values_only=True))
        wb.close()
        if not raw:
            return []
        headers = [str(c or "").strip() for c in raw[0]]
        canonical = normalize_review_csv_headers(headers)
        if canonical is None:
            raise ValueError(f"Unexpected headers in {path}: {headers!r}")
        rows = []
        for line in raw[1:]:
            if not line or not any(c is not None and str(c).strip() for c in line):
                continue
            cells = [str(c or "").strip() for c in line]
            padded = cells + [""] * (len(canonical) - len(cells))
            rows.append({h: padded[i] for i, h in enumerate(canonical)})
        return rows

    raise ValueError(f"Unsupported input: {path}")


def _answer_pool(rows: list[dict[str, str]]) -> list[str]:
    pool: list[str] = []
    for r in rows:
        text = r.get("正解テキスト", "").strip() or r.get("選択肢A", "").strip()
        if text:
            pool.append(text)
    return list(dict.fromkeys(pool))


def _three_distractors(
    qid: str,
    question: str,
    answer: str,
    pool: list[str],
    *,
    for_kids: bool,
) -> tuple[str, str, str] | None:
    kid_pool = [a for a in pool if is_kid_friendly_distractor(a)] if for_kids else pool
    work_pool = kid_pool if (for_kids and kid_pool) else pool

    dai = extract_dai_keyword(question)
    food = question_wants_food_distractors(question) and (
        answer_looks_like_food(answer) or food_mode_heuristic(question)
    )

    if dai or food:
        options, _ = build_six_options(
            question,
            answer,
            work_pool,
            _stable_rng(qid),
            for_kids=for_kids,
            fix_correct_at_a=True,
        )
        b, c, d = options[1], options[2], options[3]
    else:
        scored: list[tuple[float, str]] = []
        for cand in work_pool:
            if cand == answer:
                continue
            s = _score_candidate(
                question,
                answer,
                cand,
                dai_keyword=dai,
                food_mode=food,
                for_kids=for_kids,
            )
            if s >= 0:
                scored.append((s + _stable_rng(qid).random() * 0.35, cand))
        scored.sort(key=lambda x: (-x[0], x[1]))
        picks: list[str] = []
        seen: set[str] = set()
        for _, cand in scored:
            if cand in seen:
                continue
            seen.add(cand)
            picks.append(cand)
            if len(picks) >= 3:
                break
        if len(picks) < 3:
            return None
        b, c, d = picks[0], picks[1], picks[2]

    if not (b.strip() and c.strip() and d.strip()):
        return None
    if len({b, c, d, answer}) < 4:
        return None
    return b, c, d


def fill_rows(
    rows: list[dict[str, str]],
    *,
    for_kids: bool = True,
    overwrite: bool = False,
) -> tuple[list[dict[str, str]], int, int]:
    pool = _answer_pool(rows)
    filled = 0
    skipped = 0
    out: list[dict[str, str]] = []

    for row in rows:
        r = dict(row)
        answer = r.get("選択肢A", "").strip() or r.get("正解テキスト", "").strip()
        if not answer:
            out.append(r)
            skipped += 1
            continue

        has_manual = any(r.get(k, "").strip() for k in ("選択肢B", "選択肢C", "選択肢D"))
        if has_manual and not overwrite:
            if not r.get("正解記号", "").strip():
                r["正解記号"] = CORRECT_ANSWER_SYMBOL
            if not r.get("正解テキスト", "").strip():
                r["正解テキスト"] = answer
            out.append(r)
            continue

        triple = _three_distractors(
            r.get("ID", ""),
            r.get("問題文", ""),
            answer,
            pool,
            for_kids=for_kids,
        )
        if triple is None:
            if overwrite:
                r["選択肢B"] = ""
                r["選択肢C"] = ""
                r["選択肢D"] = ""
            skipped += 1
        else:
            r["選択肢B"], r["選択肢C"], r["選択肢D"] = triple
            filled += 1

        if not r.get("正解記号", "").strip():
            r["正解記号"] = CORRECT_ANSWER_SYMBOL
        if not r.get("正解テキスト", "").strip():
            r["正解テキスト"] = answer

        out.append(r)

    return out, filled, skipped


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(REVIEW_CSV_HEADERS))
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in REVIEW_CSV_HEADERS})


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill review CSV B/C/D distractors")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--for-kids",
        action="store_true",
        default=True,
        help="easy 向けの誤答フィルタ（既定: on）",
    )
    parser.add_argument(
        "--no-for-kids",
        action="store_false",
        dest="for_kids",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    rows = _read_rows(args.input)
    filled_rows, filled, skipped = fill_rows(
        rows, for_kids=args.for_kids, overwrite=args.overwrite
    )
    write_csv(args.output, filled_rows)
    print(f"Wrote {args.output} ({len(filled_rows)} rows, filled={filled}, skipped={skipped})")


if __name__ == "__main__":
    main()
