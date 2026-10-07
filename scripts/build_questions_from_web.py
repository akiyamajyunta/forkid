"""
なぞなぞデータ生成（https://nazonazo.nihonsimondai.com/ より最大300問）。

実行: python scripts/build_questions_from_web.py
"""
from __future__ import annotations

import json
import random
import re
import urllib.request
from html import unescape
from pathlib import Path

from dev_explanation import make_dev_explanation
from contextual_hint import make_contextual_hint

BASE_URL = "https://nazonazo.nihonsimondai.com/"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "questions.json"
TARGET_COUNT = 300
SOURCE_NOTE = "nazonazo.nihonsimondai.com"

_QA_RE = re.compile(
    r"<p>\s*(\d+)\.\s*(.+?)\s*<br\s*/?\s*>\s*<br\s*/?\s*>\s*"
    r'<span[^>]*onmouseover="this\.innerText=\'([^\']*)\';"',
    re.DOTALL | re.IGNORECASE,
)


def page_urls() -> list[str]:
    urls = [BASE_URL + "index.html"]
    for start in range(21, 301, 20):
        urls.append(f"{BASE_URL}nazo{start}.html")
    return urls


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "kidgame-builder/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_page(html: str) -> list[tuple[int, str, str]]:
    items: list[tuple[int, str, str]] = []
    for num_s, q_raw, ans_raw in _QA_RE.findall(html):
        q = clean_text(q_raw)
        a = clean_text(ans_raw)
        if q and a and a != "↑の答え":
            items.append((int(num_s), q, a))
    return items


def assign_levels(num: int, question: str, answer: str) -> list[str]:
    """内容・番号から出題レベルを付与（複数可）。"""
    levels: set[str] = set()
    q_len = len(question)
    a_len = len(answer)

    abstract_markers = (
        "数学",
        "論理",
        "ギリシャ",
        "一生",
        "音を",
        "「",
        "同時",
        "関係",
    )
    kid_friendly = (
        "友達",
        "おうち",
        "おてんとう",
        "朝",
        "夜",
        "家",
        "窓",
    )

    complexity = 0
    if q_len >= 42:
        complexity += 1
    if q_len >= 55:
        complexity += 1
    if a_len >= 6:
        complexity += 1
    if any(m in question for m in abstract_markers):
        complexity += 2
    if any(m in question for m in kid_friendly):
        complexity -= 1

    # 若い番号ほど易しめ、後半ほど難しめ（サイト構成に沿う）
    if num <= 120 or (complexity <= 0 and a_len <= 4):
        levels.add("easy")
    if 80 <= num <= 240 or complexity <= 1:
        levels.add("normal")
    if num >= 180 or complexity >= 1:
        levels.add("hard")

    if not levels:
        levels.add("normal")
    order = ["easy", "normal", "hard"]
    return [lv for lv in order if lv in levels]


def _good_distractor(text: str) -> bool:
    if len(text) > 14:
        return False
    if "（" in text or "(" in text:
        return False
    if "漢字" in text or "返答" in text:
        return False
    return True


def build_options(answer: str, all_answers: list[str], rng: random.Random) -> tuple[list[str], int]:
    pool = [a for a in all_answers if a != answer and _good_distractor(a)]
    if len(pool) < 5:
        pool = [a for a in all_answers if a != answer]
    rng.shuffle(pool)
    distractors: list[str] = []
    for cand in pool:
        if cand in distractors:
            continue
        distractors.append(cand)
        if len(distractors) == 5:
            break
    fallbacks = ["わからない", "えーっと", "パソコン", "くつ", "かばん", "えんぴつ"]
    for fb in fallbacks:
        if len(distractors) >= 5:
            break
        if fb != answer and fb not in distractors:
            distractors.append(fb)
    options = [answer] + distractors[:5]
    rng.shuffle(options)
    return options, options.index(answer)


def main() -> None:
    collected: dict[int, tuple[str, str]] = {}
    for url in page_urls():
        html = fetch_html(url)
        for num, q, a in parse_page(html):
            collected[num] = (q, a)
        if len(collected) >= TARGET_COUNT:
            break

    nums = sorted(n for n in collected if n <= TARGET_COUNT)[:TARGET_COUNT]
    if len(nums) < TARGET_COUNT:
        raise SystemExit(f"Expected {TARGET_COUNT} questions, got {len(nums)}")

    answers = [collected[n][1] for n in nums]
    rng = random.Random(20260324)
    questions: list[dict] = []

    for num in nums:
        q, a = collected[num]
        options, answer_index = build_options(a, answers, rng)
        levels = assign_levels(num, q, a)
        questions.append(
            {
                "id": f"web_{num:03d}",
                "levels": levels,
                "question": q,
                "options": options,
                "answer_index": answer_index,
                "hint": make_contextual_hint(q, a, num),
                "dev_explanation": make_dev_explanation(q, a, num),
                "source": SOURCE_NOTE,
                "source_no": num,
            }
        )

    payload = {
        "meta": {
            "source": SOURCE_NOTE,
            "url": BASE_URL,
            "count": len(questions),
            "license_note": "教育・私的利用向けにゲーム内で利用。出典サイトを参照。",
        },
        "questions": questions,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(questions)} questions to {OUT_PATH}")


if __name__ == "__main__":
    main()
