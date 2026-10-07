from __future__ import annotations

import json
import re
import urllib.request
from html import unescape
from pathlib import Path

from audit_questions import QA_RE, clean, fetch_collected, urls  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "source_qa.json"


def main() -> None:
    collected = fetch_collected()
    items = [
        {"no": n, "question": collected[n][0], "answer": collected[n][1]}
        for n in sorted(collected.keys())
        if n <= 300
    ]
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(len(items), OUT)


if __name__ == "__main__":
    main()
