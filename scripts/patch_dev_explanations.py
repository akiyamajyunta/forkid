"""既存 questions.json に dev_explanation だけ付与（再スクレイプなし）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dev_explanation import make_dev_explanation  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "questions.json"


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    for q in data.get("questions", []):
        num = int(q.get("source_no", 0))
        answer = q["options"][q["answer_index"]]
        if num > 0:
            q["dev_explanation"] = make_dev_explanation(q["question"], answer, num)
        elif "dev_explanation" not in q:
            q["dev_explanation"] = make_dev_explanation(
                q["question"],
                answer,
                0,
            )
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Patched {len(data['questions'])} dev_explanation fields")


if __name__ == "__main__":
    main()
