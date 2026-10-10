"""
nazoq.com から取得 → review CSV（正答は選択肢A、B/C/D 空欄）と questions.json（6択生成）

実行:
  python scripts/build_questions_from_nazoq.py --only easy   # easy/all → questions_review_easy.csv
  python scripts/build_questions_from_nazoq.py               # 全難易度
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kidgame.data.models import Difficulty
from kidgame.data.review_csv import (
    REVIEW_CSV_HEADERS,
    options_to_review_row_fields,
    review_csv_path,
)
from nazoq_scraper import (
    ENTRY_ID_RE,
    collect_entry_urls,
    fetch_html,
    iter_items,
    list_page_urls,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_JSON = DATA_DIR / "questions.json"
SOURCE_NOTE = "nazoq.com"

GAME_LEVEL_SOURCES: dict[str, tuple[str, ...]] = {
    "easy": ("easy",),  # https://nazoq.com/easy/all/
    "normal": ("normal",),
    "hard": ("hard",),  # https://nazoq.com/hard/all/
}


def _qid_from_url(url: str) -> str | None:
    m = ENTRY_ID_RE.search(url)
    return f"nazoq_{m.group(1)}" if m else None


def _load_review_csv_ids(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    ids: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = (row.get("ID") or "").strip()
            if qid:
                ids.add(qid)
    return ids


def _filter_urls_skip_ids(urls: list[str], skip_ids: set[str]) -> list[str]:
    if not skip_ids:
        return urls
    out: list[str] = []
    for url in urls:
        qid = _qid_from_url(url)
        if qid and qid not in skip_ids:
            out.append(url)
    return out


def _collect_urls(site_levels: tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for level in site_levels:
        for url in collect_entry_urls(fetch_html(list_page_urls(level))):
            if url not in seen:
                seen.add(url)
                ordered.append(url)
    return ordered


def _write_sparse_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(REVIEW_CSV_HEADERS)
        for row in rows:
            w.writerow(
                options_to_review_row_fields(
                    row["id"],
                    row["question"],
                    row["answer"],
                    row["hint"],
                    row.get("dev_explanation", ""),
                )
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=300)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--only", choices=tuple(GAME_LEVEL_SOURCES.keys()))
    parser.add_argument(
        "--output",
        type=Path,
        help="出力 CSV（例: data/questions_review_easy_no2.csv）",
    )
    parser.add_argument(
        "--skip-ids-from",
        type=Path,
        action="append",
        default=[],
        help="この review CSV に含まれる ID は取得しない（複数指定可）",
    )
    parser.add_argument("--seed", type=int, default=20261008)
    args = parser.parse_args()

    targets = (
        {args.only: GAME_LEVEL_SOURCES[args.only]}
        if args.only
        else GAME_LEVEL_SOURCES
    )

    if args.output and len(targets) != 1:
        parser.error("--output は --only と併用してください")
    out_csv = args.output
    if out_csv and not out_csv.is_absolute():
        out_csv = DATA_DIR / out_csv

    skip_ids: set[str] = set()
    for p in args.skip_ids_from:
        path = p if p.is_absolute() else DATA_DIR / p
        skip_ids |= _load_review_csv_ids(path)

    by_level: dict[str, list[dict]] = {}
    for game_level, site_levels in targets.items():
        print(f"=== {game_level} ===")
        urls = _collect_urls(site_levels)
        if skip_ids:
            urls = _filter_urls_skip_ids(urls, skip_ids)
            print(f"  candidate URLs after skip: {len(urls)}")
        items = iter_items(urls, delay=args.delay, max_count=args.max)
        print(f"  fetched {len(items)}")
        by_level[game_level] = [
            {
                "id": it.qid,
                "question": it.question,
                "answer": it.answer,
                "hint": it.hint,
                "dev_explanation": f"出典: {it.url} / サイトレベル: {it.site_level}",
                "source_url": it.url,
            }
            for it in items
        ]
        dest = out_csv or review_csv_path(DATA_DIR, Difficulty(game_level))
        _write_sparse_csv(dest, by_level[game_level])
        print(f"  CSV -> {dest}")

    if args.only:
        print("import: python scripts/import_review_csv.py")
        return

    from kidgame.data.review_csv import load_question_bank_from_review_csvs

    bank = load_question_bank_from_review_csvs(DATA_DIR)
    questions = []
    for q in bank.questions:
        questions.append(
            {
                "id": q.id,
                "levels": sorted(d.value for d in q.levels),
                "question": q.question,
                "options": list(q.options),
                "answer_index": 0,
                "hint": q.hint,
                "dev_explanation": q.dev_explanation,
                "source": SOURCE_NOTE,
            }
        )
    payload = {
        "meta": {
            "source": SOURCE_NOTE,
            "url": "https://nazoq.com/",
            "count": len(questions),
            "review_csv_format": "correct_always_A_sparse_bcd",
            "imported_from": "build_questions_from_nazoq.py",
        },
        "questions": questions,
    }
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"JSON -> {OUT_JSON} ({len(questions)} questions)")


if __name__ == "__main__":
    main()
