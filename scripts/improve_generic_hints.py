"""hints_by_no.json の汎用ヒントを contextual ロジックで差し替え。"""

from __future__ import annotations

import json
import re
from pathlib import Path

from contextual_hint import _pun_family_hint, make_contextual_hint
from hint_generator import _ANSWER_HINTS

ROOT = Path(__file__).resolve().parents[1]
HINTS_PATH = ROOT / "data" / "hints_by_no.json"
SOURCE_PATH = ROOT / "data" / "source_qa.json"

GENERIC_RE = re.compile(
    r"身の まわり|言葉 や 数|ダジャレ かも|考えてみて$"
)


def _hint_without_by_no(question: str, answer: str, source_no: int) -> str:
    """make_contextual_hint と同系だが hints_by_no を参照しない。"""
    from contextual_hint import _overrides  # noqa: PLC0415

    key = str(source_no)
    ov = _overrides().get(key, {})
    if ov.get("hint"):
        return ov["hint"]
    a = answer.strip()
    if a in _ANSWER_HINTS:
        return _ANSWER_HINTS[a]
    pun = _pun_family_hint(question, a)
    if pun:
        return pun
    if "（" in a or "(" in a:
        return "ことば の 音 や 漢字 の 数 で ひっかける なぞ だよ。声に 出して 考えてみて"
    return make_contextual_hint(question, answer, source_no)


def main() -> None:
    source = {x["no"]: x for x in json.loads(SOURCE_PATH.read_text(encoding="utf-8"))}
    hints = json.loads(HINTS_PATH.read_text(encoding="utf-8"))
    replaced = 0
    for no in range(1, 301):
        key = str(no)
        cur = hints.get(key, "")
        if not GENERIC_RE.search(cur):
            continue
        item = source[no]
        new = _hint_without_by_no(item["question"], item["answer"], no)
        if new != cur and not GENERIC_RE.search(new):
            hints[key] = new
            replaced += 1
        elif GENERIC_RE.search(new):
            # まな板系など
            q, a = item["question"], item["answer"]
            if "まな板" in q:
                hints[key] = "まな板 で 使う 切る キッチン 道具 だよ"
                replaced += 1
            elif "板" in q and "上" in q:
                hints[key] = "板 の 上 に 関係 する 道具 や 言葉 だよ"
                replaced += 1
    HINTS_PATH.write_text(json.dumps(hints, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"replaced {replaced} generic hints in {HINTS_PATH}")


if __name__ == "__main__":
    main()
