"""POST HOC (not in the frozen protocol): recall_H if a maintainer reads only the first k problems of each list.
Locates each matched item's adjudicator quote in the numbered list; unlocatable quotes are reported."""
import json, re, glob, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = {}
for f in sorted(glob.glob(str(ROOT / "adjudication/verdicts_*.json"))): V.update(json.load(open(f)))
KEY = json.load(open(ROOT / "adjudication/units_key.json"))
H = [f"H{i:02d}" for i in range(1, 12)]
texts = {}
for b in sorted(glob.glob(str(ROOT / "adjudication/batch_*.md"))):
    for part in open(b).read().split("=== CRITIQUE ")[1:]:
        uid, rest = part.split(" ", 1)
        if rest.startswith("START"): texts[uid] = rest.split("\n", 1)[1]
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
out = {}
for u in KEY:
    if u["part"] not in ("problems", "list") or u["arm"] == "control": continue
    items = re.split(r"(?m)^\s*(?:\*\*)?\d+[.)]\s", texts[u["uid"]])[1:]
    pos, miss = {}, []
    for it in H:
        v = V[u["uid"]][it]
        if not v["match"]: continue
        q = norm(v["quote"])[:60]
        idx = next((n for n, t in enumerate(items, 1) if q and q[:40] in norm(t)), None)
        if idx is None: miss.append(it)
        pos[it] = idx
    out.setdefault(f"{u['arm']}|{u['version']}", []).append({"n_items": len(items), "pos": pos, "unlocated": miss})
res = {}
for cell, runs in sorted(out.items()):
    row = {}
    for k in (5, 10, 15, 20):
        row[f"top{k}"] = round(st.mean(sum(1 for p in r["pos"].values() if p is not None and p <= k) / 11 for r in runs), 3)
    row["all"] = round(st.mean(len(r["pos"]) / 11 for r in runs), 3)
    row["unlocated"] = sum(len(r["unlocated"]) for r in runs); row["mean_items"] = round(st.mean(r["n_items"] for r in runs), 1)
    res[cell] = row
(ROOT / "posthoc_topk.json").write_text(json.dumps({"label": "POST HOC exploratory; not used for the ruling", "cells": res, "runs": out}, indent=1) + "\n")
for c, r in res.items(): print(c, r)
