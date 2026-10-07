"""
source_qa.json と curated_overrides を questions.json に反映する。

- 問題文・正答を出典と一致させる
- ヒントを contextual_hint で再生成
- dev_explanation を更新
"""

from __future__ import annotations

import json
from pathlib import Path

from contextual_hint import make_contextual_hint
from dev_explanation import make_dev_explanation

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "questions.json"
SOURCE_PATH = ROOT / "data" / "source_qa.json"
OVERRIDES_PATH = Path(__file__).resolve().parent / "curated_overrides.json"


def main() -> None:
    source = {item["no"]: item for item in json.loads(SOURCE_PATH.read_text(encoding="utf-8"))}
    overrides = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    for q in data["questions"]:
        no = int(q.get("source_no", 0))
        if no not in source:
            continue
        src = source[no]
        ov = overrides.get(str(no), {})

        q["question"] = ov.get("question", src["question"])
        canonical = ov.get("answer", src["answer"])

        opts = list(q["options"])
        idx = int(q["answer_index"])
        if 0 <= idx < len(opts):
            opts[idx] = canonical
        else:
            opts.append(canonical)
            idx = len(opts) - 1
        q["options"] = opts
        q["answer_index"] = idx

        q["hint"] = make_contextual_hint(q["question"], canonical, no)
        q["dev_explanation"] = make_dev_explanation(q["question"], canonical, no)

    data.setdefault("meta", {})["hints_style"] = "hints_by_no_v1"
    data["meta"]["reconciled"] = True
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Reconciled {len(data['questions'])} questions -> {JSON_PATH}")


if __name__ == "__main__":
    main()
