"""CPU pre-flight: every frame row builds all arm messages (identity asserts) and the copied first-run message
reproduces each recorded prompt_sha256 byte for byte. usage: check_messages.py FIRST_RUN_DIR out.json"""
import json, sys, collections, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fvep
d = pathlib.Path(sys.argv[1])
res = collections.Counter()
for fr, raw in (("out/frame.jsonl", "out/carbon_raw.jsonl"), ("out/controls_frame.jsonl", "out/ctrl_raw.jsonl")):
    rec = {}
    for l in open(d / raw):
        x = json.loads(l); rec[x["id"]] = x["prompt_sha256"]
    for l in open(d / fr):
        r = json.loads(l)
        st = r["stratum"].split("|")[0]
        if st == "STRICT":
            continue
        for arm in ("F_plus", "F_gene"):
            fvep.frontier_message(r, arm)
        same = fvep.frontier_message(r, "F_plus") == fvep.frontier_message(r, "F_gene")
        res[f"{st}_plus_eq_gene_{r['oriented']}_{same}"] += 1
        res[f"{st}_orig_sha_match_{fvep.sha(fvep.original_message(r)) == rec.get(r['id'])}"] += 1
json.dump(dict(sorted(res.items())), open(sys.argv[2], "w"), indent=1)
print(dict(sorted(res.items())))
