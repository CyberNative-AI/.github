"""Build the two merged verdict columns from the raw judge outputs (added for the public copy).

usage: python3 -I src/merge.py <verdicts-dir> <records.jsonl>

<verdicts-dir> holds verdicts.jsonl (all records, 6 s), verdicts_t6w1.jsonl (the timed-out
records re-judged one at a time at 6 s) and verdicts_t18.jsonl (the same records at 18 s).
Writes verdicts_t6fix.jsonl (verdicts.jsonl with the records that PASS in t6w1 replaced) and
verdicts_t18full.jsonl (verdicts.jsonl with every t18 record replaced), in verdicts.jsonl's
order. Stops unless verdicts.jsonl covers every record exactly once with matching code hashes,
and unless every replacement row's code hash matches too; on any failure it writes nothing.
"""
import json, sys
def load(p):
    return {json.loads(l)["key"]: l for l in open(p, encoding="utf-8")}
d = sys.argv[1]
base = [json.loads(l)["key"] for l in open(f"{d}/verdicts.jsonl", encoding="utf-8")]
full = load(f"{d}/verdicts.jsonl")
w1 = {k: l for k, l in load(f"{d}/verdicts_t6w1.jsonl").items() if json.loads(l)["verdict"] == "PASS"}
t18 = load(f"{d}/verdicts_t18.jsonl")
recs = {json.loads(l)["key"]: json.loads(l)["code_sha256"] for l in open(sys.argv[2], encoding="utf-8")}
assert len(base) == len(set(base)) == len(recs) and set(base) == set(recs), "verdicts.jsonl must cover every record once"
for k in base:
    assert json.loads(full[k])["code_sha256"] == recs[k], f"verdicts.jsonl code hash differs: {k}"
outputs = {}
for name, sub in (("verdicts_t6fix.jsonl", w1), ("verdicts_t18full.jsonl", t18)):
    assert set(sub) <= set(full), f"{name}: replacement keys missing from verdicts.jsonl"
    lines = []
    for k in base:
        line = sub.get(k, full[k])
        assert json.loads(line)["code_sha256"] == recs[k], f"{name}: code hash differs: {k}"
        lines.append(line)
    outputs[name] = (lines, len(sub))
for name, (lines, n) in outputs.items():  # written only after every check passed
    with open(f"{d}/{name}", "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)
    print(name, len(base), "rows,", n, "replaced")
