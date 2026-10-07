"""出典サイトの正答と JSON を照合し、汎用ヒントを一覧する。"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "questions.json"
BASE = "https://nazonazo.nihonsimondai.com/"

QA_RE = re.compile(
    r"<p>\s*(\d+)\.\s*(.+?)\s*<br\s*/?\s*>\s*<br\s*/?\s*>\s*"
    r"<span[^>]*onmouseover=\"this\.innerText='([^']*)';\"",
    re.DOTALL | re.IGNORECASE,
)

GENERIC_HINTS = {
    "同じ 言葉 でも 意味 が 2通り ある かも",
    "声 に 出して 読む と ヒント に なる こと も",
    "身の 回り と 言葉 の ダジャレ を 考えてみて",
    "食べ物・動物・道具 の どれ でも ない 答え かも",
    "字面 どおり じゃ ない 読み方 がある よ",
}


def urls() -> list[str]:
    out = [BASE + "index.html"]
    for start in range(21, 301, 20):
        out.append(f"{BASE}nazo{start}.html")
    return out


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def fetch_collected() -> dict[int, tuple[str, str]]:
    collected: dict[int, tuple[str, str]] = {}
    for url in urls():
        req = urllib.request.Request(url, headers={"User-Agent": "kidgame-audit/1.0"})
        html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        for num_s, q, a in QA_RE.findall(html):
            collected[int(num_s)] = (clean(q), clean(a))
    return collected


def main() -> None:
    collected = fetch_collected()
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    mismatches: list[str] = []
    generic: list[str] = []
    for q in data["questions"]:
        no = int(q.get("source_no", 0))
        json_ans = q["options"][q["answer_index"]]
        if no in collected:
            _, web_ans = collected[no]
            if web_ans != json_ans:
                mismatches.append(f"{no}\t{q['id']}\tweb={web_ans}\tjson={json_ans}")
        if q.get("hint", "") in GENERIC_HINTS:
            generic.append(f"{no}\t{q['id']}\t{json_ans}\t{q['hint']}")

    report = ROOT / "data" / "audit_report.txt"
    lines = [
        f"mismatches: {len(mismatches)}",
        *mismatches,
        "",
        f"generic_hints: {len(generic)}",
        *generic,
    ]
    report.write_text("\n".join(lines), encoding="utf-8")
    print(report)
    print(f"mismatches={len(mismatches)} generic_hints={len(generic)}")


if __name__ == "__main__":
    main()
