"""data/pun_hints_batch.json を hints_by_no.json にマージする。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "data" / "pun_hints_batch.json"
HINTS = ROOT / "data" / "hints_by_no.json"


def main() -> None:
    batch = json.loads(BATCH.read_text(encoding="utf-8"))
    hints = json.loads(HINTS.read_text(encoding="utf-8"))
    for key, text in batch.items():
        hints[key] = text
    HINTS.write_text(json.dumps(hints, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"merged {len(batch)} hints -> {HINTS}")


if __name__ == "__main__":
    main()
