"""OpenAI math release: release formalization catalogue vs first correction round. Usage: analyze.py REPO_DIR [RELEASE_COMMIT UPDATE_COMMIT]"""
import json, math, re, subprocess, sys
from pathlib import Path

REL, UPD = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else ("adc7f12", "3014888")
repo = Path(sys.argv[1])
def git(*a): return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout

rel_dirs = sorted(l.split("/", 1)[1] for l in git("ls-tree", "-d", "--name-only", REL, "preprints/").split())
upd_dirs = sorted(l.split("/", 1)[1] for l in git("ls-tree", "-d", "--name-only", UPD, "preprints/").split())
cat = git("show", f"{REL}:lean/formalization.yaml")
cat_dirs = set(re.findall(r"id:\s*\.\./preprints/([^/\s]+)/", cat))
assert cat_dirs <= set(rel_dirs), cat_dirs - set(rel_dirs)

SUBST = re.compile(r"repairs|corrects|supplies|adds |states .* explicitly|clarifies|restricts|characterizes|derives", re.I)
CITE_ONLY = re.compile(r"^This version (updates (a )?citations? to (a )?revised manuscripts? in this collection|removes an obsolete supporting citation and updates citations to revised manuscripts in this collection);", re.I)
rows = []
for d in sorted(set(upd_dirs) - set(rel_dirs)):
    readme = git("show", f"{UPD}:preprints/{d}/README.md")
    note = readme.split("## Version note", 1)[1].strip().split("\n")[0]
    prev = re.search(r"\(\.\./([^/]+)/", note).group(1)
    cls = "CITATION-ONLY" if CITE_ONLY.match(note) else ("REPAIRED" if SUBST.search(note) else "UNCLASSIFIED")
    rows.append({"new": d, "prev": prev, "class": cls, "in_release_catalogue": prev in cat_dirs, "note": note})
hist = git("show", f"{UPD}:history.md")
withdrawn_titles = re.findall(r"^- (.+)$", hist.split("**Withdrawals**", 1)[1].split("**Fixes**", 1)[0], re.M)
mod_readmes = [l.split("/")[1] for l in git("diff", "--name-only", REL, UPD).split() if re.match(r"preprints/[^/]+/README\.md$", l) and l.split("/")[1] in rel_dirs]
for d in sorted(mod_readmes):
    rows.append({"new": None, "prev": d, "class": "WITHDRAWN", "in_release_catalogue": d in cat_dirs, "note": git("show", f"{UPD}:preprints/{d}/README.md")[:400]})

def binom_le(k, n, p): return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k + 1))
n_rel, n_cat = len(rel_dirs), len(cat_dirs); p0 = n_cat / n_rel
out = {"release_commit": REL, "update_commit": UPD, "release_dirs": n_rel, "release_catalogue_dirs": n_cat, "p0": p0,
       "withdrawn_titles_history_md": withdrawn_titles, "rows": rows, "summary": {}}
for name, sel in [("affected", {"WITHDRAWN", "REPAIRED"}), ("withdrawn", {"WITHDRAWN"}), ("repaired", {"REPAIRED"}), ("citation_only", {"CITATION-ONLY"}), ("unclassified", {"UNCLASSIFIED"})]:
    g = [r for r in rows if r["class"] in sel]; k = sum(r["in_release_catalogue"] for r in g); n = len(g)
    out["summary"][name] = {"k": k, "n": n, "P_le_k": binom_le(k, n, p0) if n else None, "P_ge_k": 1 - binom_le(k - 1, n, p0) if n and k else 1.0}
json.dump(out, sys.stdout, indent=1, sort_keys=True)
