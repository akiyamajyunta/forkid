import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = {x["no"]: x for x in json.loads((ROOT / "data/source_qa.json").read_text(encoding="utf-8"))}
hints = json.loads((ROOT / "data/hints_by_no.json").read_text(encoding="utf-8"))
pat = re.compile(r"身の まわり|言葉 や 数")
generic_nos = [no for no in range(1, 301) if pat.search(hints.get(str(no), ""))]
print("total", len(generic_nos))
out = ROOT / "data" / "generic_hints_list.txt"
lines = [f"{no}\t{src[no]['answer']}\t{src[no]['question']}" for no in generic_nos]
out.write_text("\n".join(lines), encoding="utf-8")
print("wrote", out)
for no in generic_nos[:20]:
    s = src[no]
    print(no, s["answer"], s["question"][:60], sep="\t")
