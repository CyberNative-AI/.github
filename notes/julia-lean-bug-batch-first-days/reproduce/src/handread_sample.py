"""Seeded sample (random.Random(17382), up to 30) of O_prior items closed-unaccepted at 72 h; fetch comments; digest."""
import datetime as dt, json, pathlib, random, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fetch as fe, compute as co
out = pathlib.Path(sys.argv[1])
rt = co.t(json.loads((out / "data" / "fetch-meta.json").read_text())["read_time"])
rows = [json.loads(l) for l in open(out / "data" / "items.jsonl")]
pool = sorted([r for r in rows if r["group"] == "O_prior" and co.outcome(r, 72, rt) in ("CLOSED_UNACCEPTED", "NOT_PLANNED", "COMPLETED_NOFIX")], key=lambda r: r["number"])
sample = random.Random(17382).sample(pool, min(30, len(pool)))
api = fe.Api(out, fe.load_token())
dig = []
for r in sorted(sample, key=lambda r: r["number"]):
    cs = api.get(f"/repos/{fe.REPO}/issues/{r['number']}/comments?per_page=100", f"comments-{r['number']}")
    dig.append({"number": r["number"], "is_pr": r["is_pr"], "outcome72": co.outcome(r, 72, rt), "state_reason": r["state_reason"],
                "closers": r.get("closers"), "title": r["title"], "assoc": r["assoc"],
                "comments": [(c["user"]["login"], c["author_association"], c["body"]) for c in cs]})
(out / "data" / "handread-sample-digest.json").write_text(json.dumps(dig, indent=1) + "\n")
print(len(pool), "pool;", len(dig), "sampled")
