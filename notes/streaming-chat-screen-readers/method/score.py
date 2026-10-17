"""Score trial JSONs (Orca 'speech' or virtual 'vsr' utterances) into announcement classes.

usage: python3 score.py <outdir> [--oracle orca|vsr] [--json out.json]
Frozen definitions (PROTOCOL.md §5):
  reply words  = lowercase word tokens of stream_text.RESPONSE ([a-z0-9]+(?:-[a-z0-9]+)*), markdown bullets dropped
  content utterance = >=50% of its word tokens are reply words AND it has >=1 reply word not in the prompt
  C = distinct reply words spoken in content utterances / distinct reply words
  E = 'zetaend' spoken in a content utterance
  R = reply-word tokens spoken in content utterances / reply word count
  trial class: NO_REPLY (C=0; '+status' if any non-content utterance matches STATUS_RE)
               PARTIAL (0<C<0.9 or not E) | ONCE (C>=0.9, E, R<=1.5) | REPEATED (C>=0.9, E, R>1.5)
  unit class = class held by >=2 of 3 trials, else MIXED; trial with error or endSeen false = INVALID_TRIAL
"""
import json, re, sys, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "apps"))
from stream_text import RESPONSE
WORD = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
REPLY = WORD.findall(RESPONSE.lower())
REPLY_SET = set(REPLY)
PROMPT_SET = set(WORD.findall("tell me about lyon"))
STATUS_RE = re.compile(r"generat|typing|thinking|respon|loading|busy|running|complete|done|wait|stop", re.I)

def utterances(rec, oracle):
    if oracle == "orca":
        return [u["text"] for u in rec.get("speech") or []]
    return [re.sub(r"^(polite|assertive):\s*", "", s) for s in rec.get("vsr") or [] if re.match(r"^(polite|assertive):", s)]

def score_trial(rec, oracle):
    if rec.get("error") or not rec.get("endSeen"):
        return {"cls": "INVALID_TRIAL"}
    us = utterances(rec, oracle)
    content, other = [], []
    for u in us:
        w = WORD.findall(u.lower())
        inr = [x for x in w if x in REPLY_SET]
        if w and len(inr) / len(w) >= 0.5 and any(x not in PROMPT_SET for x in inr):
            content.append(inr)
        else:
            other.append(u)
    spoken = set(x for c in content for x in c)
    C = len(spoken) / len(REPLY_SET)
    E = "zetaend" in spoken
    R = sum(len(c) for c in content) / len(REPLY)
    if C == 0:
        cls = "NO_REPLY+status" if any(STATUS_RE.search(o) for o in other) else "NO_REPLY"
    elif C < 0.9 or not E:
        cls = "PARTIAL"
    else:
        cls = "ONCE" if R <= 1.5 else "REPEATED"
    return {"cls": cls, "C": round(C, 3), "E": E, "R": round(R, 2), "n_content": len(content), "n_other": len(other),
            "other": other[:12], "status_like": [o for o in other if STATUS_RE.search(o)][:6]}

def main():
    outdir = pathlib.Path(sys.argv[1]); oracle = "orca"; jout = None
    if "--oracle" in sys.argv: oracle = sys.argv[sys.argv.index("--oracle") + 1]
    if "--json" in sys.argv: jout = sys.argv[sys.argv.index("--json") + 1]
    units = collections.defaultdict(list)
    for f in sorted(outdir.glob("*-t[0-9].json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        units[rec["label"]].append({"file": f.name, **score_trial(rec, oracle)})
    res = {}
    for label, trials in sorted(units.items()):
        cnt = collections.Counter(t["cls"] for t in trials if t["cls"] != "INVALID_TRIAL")
        top = cnt.most_common(1)
        ucls = top[0][0] if top and top[0][1] >= 2 else ("INVALID" if sum(cnt.values()) < 2 else "MIXED")
        res[label] = {"unit": ucls, "trials": trials}
        print(f"{label:28s} {ucls:16s} " + " | ".join(f"{t['cls']} C={t.get('C')} R={t.get('R')} n={t.get('n_content')}" for t in trials))
    if jout:
        pathlib.Path(jout).write_text(json.dumps({"oracle": oracle, "reply_words": len(REPLY), "distinct": len(REPLY_SET), "units": res}, indent=1) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
