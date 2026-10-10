"""POST-HOC sensitivity (not in frozen protocol): broaden the release formal frame to manuscripts named in lean/docs/*.md at release. Usage: sensitivity.py REPO_DIR result.json"""
import json, math, re, subprocess, sys
from pathlib import Path
repo = Path(sys.argv[1]); res = json.load(open(sys.argv[2]))
def git(*a): return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout
REL = res["release_commit"]
docs = [p for p in git("ls-tree", "--name-only", REL, "lean/docs/").split() if p.endswith(".md")]
doc_dirs, doc_of = set(), {}
for p in docs:
    for d in re.findall(r"preprints/([^/)\s]+)/", git("show", f"{REL}:{p}")):
        doc_dirs.add(d); doc_of.setdefault(d, []).append(p.split("/")[-1])
cat = set(re.findall(r"id:\s*\.\./preprints/([^/\s]+)/", git("show", f"{REL}:lean/formalization.yaml")))
rel_dirs = set(l.split("/", 1)[1] for l in git("ls-tree", "-d", "--name-only", REL, "preprints/").split())
unknown = doc_dirs - rel_dirs
frame = (doc_dirs | cat) & rel_dirs
p0 = len(frame) / len(rel_dirs)
def ble(k, n, p): return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k + 1))
out = {"docs_files": len(docs), "doc_named_dirs": len(doc_dirs & rel_dirs), "doc_named_not_in_release": sorted(unknown), "catalogue_dirs": len(cat), "union_frame": len(frame), "release_dirs": len(rel_dirs), "p0_union": p0, "summary": {}, "hits": []}
for name, sel in [("affected", {"WITHDRAWN", "REPAIRED"}), ("withdrawn", {"WITHDRAWN"}), ("repaired", {"REPAIRED"}), ("citation_only", {"CITATION-ONLY"})]:
    g = [r for r in res["rows"] if r["class"] in sel]; k = sum(r["prev"] in frame for r in g); n = len(g)
    out["summary"][name] = {"k": k, "n": n, "P_le_k": ble(k, n, p0), "P_ge_k": 1 - ble(k - 1, n, p0) if k else 1.0}
for r in res["rows"]:
    if r["prev"] in frame: out["hits"].append({"class": r["class"], "prev": r["prev"], "in_catalogue": r["prev"] in cat, "docs": doc_of.get(r["prev"], [])})
json.dump(out, sys.stdout, indent=1, sort_keys=True)
