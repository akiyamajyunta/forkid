"""出典の正答表記（括弧内の解説付き）を子ども向け表示用に短くする overrides を追記。"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source_qa.json"
OVERRIDES = Path(__file__).resolve().parent / "curated_overrides.json"


def shorten(answer: str) -> str | None:
    a = answer.strip()
    if "「" in a:
        m = re.match(r"^([^「]+)", a)
        if m and len(m.group(1).strip()) >= 1:
            return m.group(1).strip()
    if "（" in a:
        return a.split("（", 1)[0].strip()
    if "(" in a:
        return a.split("(", 1)[0].strip()
    return None


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    added = 0
    for item in source:
        no = str(item["no"])
        short = shorten(item["answer"])
        if not short or short == item["answer"]:
            continue
        cur = overrides.get(no, {})
        if cur.get("answer"):
            continue
        overrides[no] = {**cur, "answer": short}
        added += 1
    OVERRIDES.write_text(json.dumps(overrides, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"added {added} display answers -> {OVERRIDES}")


if __name__ == "__main__":
    main()
