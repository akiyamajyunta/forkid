from __future__ import annotations

import csv
import hashlib
import random
from pathlib import Path
from typing import Any

from kidgame.data.distractors import build_six_options
from kidgame.data.kid_language import is_kid_friendly_distractor
from kidgame.data.models import Difficulty, Question, QuestionBank

# 正答は選択肢Aのみ記載。B〜D は編集用枠（サイト取得時は空欄で出力）
REVIEW_CSV_HEADERS: tuple[str, ...] = (
    "ID",
    "問題文",
    "選択肢A",
    "選択肢B",
    "選択肢C",
    "選択肢D",
    "正解記号",
    "正解テキスト",
    "ヒント",
    "開発者解説",
)

# 選択肢D 追加前の CSV（読み込み互換）
_LEGACY_REVIEW_CSV_HEADERS: tuple[str, ...] = (
    "ID",
    "問題文",
    "選択肢A",
    "選択肢B",
    "選択肢C",
    "正解記号",
    "正解テキスト",
    "ヒント",
    "開発者解説",
)


def normalize_review_csv_headers(headers: list[str]) -> tuple[str, ...] | None:
    row = [h.strip() for h in headers]
    if row == list(REVIEW_CSV_HEADERS):
        return REVIEW_CSV_HEADERS
    if row == list(_LEGACY_REVIEW_CSV_HEADERS):
        return REVIEW_CSV_HEADERS
    return None

CORRECT_ANSWER_SYMBOL = "A"
_OPTION_COLUMN_KEYS = ("選択肢A", "選択肢B", "選択肢C", "選択肢D")


def _answer_index_from_symbol(symbol: str, question_id: str) -> int:
    s = (symbol or CORRECT_ANSWER_SYMBOL).strip().upper()
    if not s or s[0] not in "ABCD":
        raise ValueError(
            f"Question {question_id!r}: 正解記号は A〜D のいずれか "
            f"（got {symbol!r}）"
        )
    return ord(s[0]) - ord("A")


def options_from_review_row(row: dict[str, str]) -> tuple[list[str], int]:
    """
    review CSV の4択列からゲーム用 options（最大6枠）と answer_index を作る。

    - 画面上の選択肢は 選択肢A〜D の文字列をそのまま使う
    - 正解記号で正解列を指定（通常 A）
    - 正解テキストは開発者用（一致チェック・表示の置換はしない）
    """
    qid = row.get("ID", "?")
    answer_index = _answer_index_from_symbol(row.get("正解記号", ""), qid)
    opts = [row.get(key, "").strip() for key in _OPTION_COLUMN_KEYS]

    if not any(opts):
        raise ValueError(f"Question {qid!r}: 選択肢A〜D がすべて空です")

    if not opts[answer_index]:
        fallback = row.get("正解テキスト", "").strip()
        if fallback:
            opts[answer_index] = fallback
        else:
            raise ValueError(
                f"Question {qid!r}: 正解記号の列が空で、正解テキストもありません"
            )

    non_empty = sum(1 for o in opts if o)
    if non_empty < 3:
        raise ValueError(
            f"Question {qid!r}: 有効な選択肢が {non_empty} 件（3 件以上必要）"
        )

    while len(opts) < 6:
        opts.append("")
    return opts[:6], answer_index


REVIEW_CSV_BY_DIFFICULTY: dict[Difficulty, str] = {
    Difficulty.EASY: "questions_review_EASY.csv",
    Difficulty.NORMAL: "questions_review_normal.csv",
    Difficulty.HARD: "questions_review_HARD.csv",
}


def review_csv_path(data_dir: Path, difficulty: Difficulty) -> Path:
    return data_dir / REVIEW_CSV_BY_DIFFICULTY[difficulty]


def all_review_csvs_present(data_dir: Path) -> bool:
    return all(review_csv_path(data_dir, d).is_file() for d in Difficulty)


def _row_dict(headers: list[str], row: list[str]) -> dict[str, str]:
    padded = row + [""] * (len(headers) - len(row))
    return {h: padded[i].strip() for i, h in enumerate(headers)}


def _legacy_row_to_canonical(row: list[str], file_headers: list[str]) -> list[str]:
    """レガシー9列 CSV を 選択肢D 付き10列に揃える。"""
    if [h.strip() for h in file_headers] == list(_LEGACY_REVIEW_CSV_HEADERS):
        padded = row + [""] * (9 - len(row))
        return [
            padded[0],
            padded[1],
            padded[2],
            padded[3],
            padded[4],
            "",
            padded[5],
            padded[6],
            padded[7],
            padded[8],
        ]
    return row


def _stable_rng(question_id: str) -> random.Random:
    digest = hashlib.md5(question_id.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:8], 16))


def _expand_options_for_play(
    question_id: str,
    question: str,
    answer: str,
    answer_pool: list[str],
    *,
    for_kids: bool,
    manual_b: str,
    manual_c: str,
    manual_d: str = "",
) -> list[str]:
    manual_wrongs = [manual_b.strip(), manual_c.strip(), manual_d.strip()]
    if any(manual_wrongs):
        opts = [answer] + [w for w in manual_wrongs if w]
        while len(opts) < 6:
            opts.append("")
        return opts[:6]

    pool = answer_pool
    if for_kids:
        kid_pool = [a for a in answer_pool if is_kid_friendly_distractor(a)]
        if kid_pool:
            pool = kid_pool
    options, _ = build_six_options(
        question,
        answer,
        pool,
        _stable_rng(question_id),
        for_kids=for_kids,
        fix_correct_at_a=True,
    )
    return options


def question_dict_from_review_row(
    row: dict[str, str],
    difficulty: Difficulty,
    answer_pool: list[str],
) -> dict[str, Any]:
    manual_wrongs = [
        row.get("選択肢B", "").strip(),
        row.get("選択肢C", "").strip(),
        row.get("選択肢D", "").strip(),
    ]
    if any(manual_wrongs):
        options, answer_index = options_from_review_row(row)
    else:
        answer = (row.get("選択肢A") or row.get("正解テキスト", "")).strip()
        if not answer:
            raise ValueError(f"Question {row.get('ID')!r}: empty 選択肢A")
        options = _expand_options_for_play(
            row["ID"],
            row.get("問題文", ""),
            answer,
            answer_pool,
            for_kids=(difficulty is Difficulty.EASY),
            manual_b=row.get("選択肢B", ""),
            manual_c=row.get("選択肢C", ""),
            manual_d=row.get("選択肢D", ""),
        )
        answer_index = 0

    dev = (row.get("開発者解説", "") or "").replace(" / ", "\n")
    correct_text = row.get("正解テキスト", "").strip()
    slot_text = options[answer_index] if answer_index < len(options) else ""
    if correct_text and correct_text != slot_text:
        note = f"正解テキスト: {correct_text}"
        dev = f"{note}\n{dev}" if dev else note

    return {
        "id": row["ID"],
        "levels": [difficulty.value],
        "question": row.get("問題文", ""),
        "options": options,
        "answer_index": answer_index,
        "hint": row.get("ヒント", ""),
        "dev_explanation": dev,
    }


def _content_signature(q: Question) -> tuple[Any, ...]:
    """同一 ID を難易度ファイルで統合する際の比較（開発者解説は除外）。"""
    return (
        q.question,
        q.options,
        q.answer_index,
        q.hint,
    )


def load_question_bank_from_review_csvs(data_dir: Path) -> QuestionBank:
    """難易度別 review CSV を読み込み、同一 ID は levels を統合する。"""
    parsed: dict[Difficulty, list[dict[str, str]]] = {}

    for difficulty in Difficulty:
        path = review_csv_path(data_dir, difficulty)
        if not path.is_file():
            raise FileNotFoundError(f"Review CSV not found: {path}")
        rows: list[dict[str, str]] = []
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                raise ValueError(f"Empty review CSV: {path}") from None
            canonical = normalize_review_csv_headers(list(headers))
            if canonical is None:
                raise ValueError(
                    f"{path.name}: unexpected headers (expected {REVIEW_CSV_HEADERS!r})"
                )
            for row in reader:
                if not row or not any(cell.strip() for cell in row):
                    continue
                row_map = _row_dict(
                    list(canonical),
                    _legacy_row_to_canonical(row, headers),
                )
                if row_map.get("ID"):
                    rows.append(row_map)
        parsed[difficulty] = rows

    merged: dict[str, Question] = {}
    level_sets: dict[str, frozenset[Difficulty]] = {}

    for difficulty, rows in parsed.items():
        pool = []
        for r in rows:
            text = r.get("正解テキスト", "").strip() or r.get("選択肢A", "").strip()
            if text:
                pool.append(text)
        pool = list(dict.fromkeys(pool))
        for line_no, row_map in enumerate(rows, start=2):
            raw = question_dict_from_review_row(row_map, difficulty, pool)
            q = Question.from_dict(raw)
            qid = q.id
            if qid in merged:
                if _content_signature(merged[qid]) != _content_signature(q):
                    # 難易度別 CSV で同一 ID の本文が違う場合は先に読んだ方を採用し levels だけ統合
                    level_sets[qid] = level_sets[qid] | frozenset({difficulty})
                    continue
                level_sets[qid] = level_sets[qid] | frozenset({difficulty})
            else:
                merged[qid] = q
                level_sets[qid] = frozenset({difficulty})

    questions: list[Question] = []
    for qid, q in merged.items():
        levels = level_sets[qid]
        if levels != q.levels:
            questions.append(
                Question(
                    id=q.id,
                    levels=levels,
                    question=q.question,
                    options=q.options,
                    answer_index=q.answer_index,
                    hint=q.hint,
                    ruby=q.ruby,
                    options_ruby=q.options_ruby,
                    hint_ruby=q.hint_ruby,
                    source=q.source,
                    source_no=q.source_no,
                    dev_explanation=q.dev_explanation,
                )
            )
        else:
            questions.append(q)

    questions.sort(key=lambda q: (q.id,))
    return QuestionBank(questions=tuple(questions))


def options_to_review_row_fields(
    qid: str,
    question: str,
    answer: str,
    hint: str,
    dev_explanation: str = "",
    *,
    opt_b: str = "",
    opt_c: str = "",
    opt_d: str = "",
) -> list[str]:
    """CSV 行。正答は常に選択肢A。"""
    dev = dev_explanation.replace("\n", " / ")
    return [
        qid,
        question,
        answer,
        opt_b,
        opt_c,
        opt_d,
        CORRECT_ANSWER_SYMBOL,
        answer,
        hint,
        dev,
    ]


def question_to_review_row(q: dict[str, Any]) -> list[str]:
    opts = [str(o) for o in q["options"]]
    ai = int(q.get("answer_index", 0))
    correct = opts[ai] if opts and 0 <= ai < len(opts) else str(q.get("correct_answer", ""))
    cells = ["", "", "", ""]
    for i in range(4):
        if i < len(opts) and opts[i].strip():
            cells[i] = opts[i]
    if correct:
        cells[ai] = correct
    symbol = chr(ord("A") + ai) if 0 <= ai <= 3 else CORRECT_ANSWER_SYMBOL
    dev = str(q.get("dev_explanation", "")).replace("\n", " / ")
    return [
        str(q.get("id", "")),
        str(q.get("question", "")),
        cells[0],
        cells[1],
        cells[2],
        cells[3],
        symbol,
        correct,
        str(q.get("hint", "")),
        dev,
    ]


def question_in_mode(q: dict[str, Any], mode: Difficulty) -> bool:
    if "levels" in q:
        return mode.value in q["levels"]
    return str(q.get("difficulty", "")).lower() == mode.value
