"""questions.json の hint のみ更新（再スクレイプなし）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contextual_hint import make_contextual_hint  # noqa: E402

JSON_PATH = Path(__file__).resolve().parents[1] / "data" / "questions.json"


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    for q in data["questions"]:
        answer = q["options"][q["answer_index"]]
        num = int(q.get("source_no", 0))
        q["hint"] = make_contextual_hint(q["question"], answer, num)
    data.setdefault("meta", {})["hints_style"] = "contextual_v3"
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated hints for {len(data['questions'])} questions")


if __name__ == "__main__":
    main()
