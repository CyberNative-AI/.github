"""Tokenizer control on the live server: for 6 frame rows (3 plus, 3 minus genes; F_plus and F_gene) tokenize the
FrontierVEP message with the window bare and wrapped in <dna></dna>. Pass iff both give identical ids, the window is
1,365 6-mer ids + 1 tail id inside <dna></dna>, and every DNA id is in the DNA range. usage: FRAME_DIR=<dir with frame.jsonl> tokcheck.py PORT out.json"""
import json, os, pathlib, sys, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fvep
R17301 = pathlib.Path(os.environ.get("FRAME_DIR", "."))
port = int(sys.argv[1])
DNA_LO, DNA_HI = 151669, 157183  # DNA token id range, from the first run's tokenizer check

def tok(text):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/tokenize",
                                 json.dumps({"content": text, "add_special": False, "with_pieces": True}).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)["tokens"]

rows = [json.loads(l) for l in open(R17301 / "frame.jsonl")]
pick = [r for r in rows if r["stratum"].startswith("M|") and r["oriented"] == "plus"][:3] + \
       [r for r in rows if r["stratum"].startswith("M|") and r["oriented"] == "minus"][:3]
res = []
for r in pick:
    for arm in ("F_plus", "F_gene"):
        a = tok(fvep.frontier_message(r, arm))
        b = tok(fvep.frontier_message(r, arm, wrap=True))
        ida = [t["id"] for t in a]
        dna = [t for t in a if DNA_LO <= t["id"] <= DNA_HI]
        pieces = [t["piece"] for t in a]
        res.append({"id": r["id"], "arm": arm, "n_tokens": len(a), "bare_eq_wrapped": ida == [t["id"] for t in b],
                    "dna_range_ids": len(dna), "dna_open": pieces.count("<dna>"), "dna_close": pieces.count("</dna>"),
                    "head": pieces[:12], "tail": pieces[-12:]})
ok = all(x["bare_eq_wrapped"] and x["dna_open"] == 1 and x["dna_close"] == 1 and x["dna_range_ids"] >= 1366 + 2
         for x in res)
json.dump({"pass": ok, "rows": res}, open(sys.argv[2], "w"), indent=1)
print("TOKCHECK", "PASS" if ok else "FAIL", [(x["id"], x["arm"], x["n_tokens"], x["dna_range_ids"], x["bare_eq_wrapped"]) for x in res])
sys.exit(0 if ok else 3)
