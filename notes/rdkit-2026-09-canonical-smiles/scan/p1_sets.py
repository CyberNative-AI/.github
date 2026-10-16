"""Molecules with more than one canonical SMILES in one release and one in the other (dbscan.py output).
usage: python p1_sets.py IN_TSV OLD_DIR NEW_DIR [BOTH_JSON] > P1_sets.json
IN_TSV is the dbscan.py input; each DIR holds part.0?.jsonl from dbscan.py.
regression: one string in OLD, several in NEW (strings and fixpoint flags from NEW); fixed: the reverse.
BOTH_JSON, if given, gets the molecules with several strings in both releases (strings from OLD, then NEW).
Stops with exit 1 unless both DIRs hold exactly one record per input ID and the only errors are
parse failures common to both releases."""
import json, sys
from pathlib import Path


def fail(msg):
    sys.exit(f"p1_sets.py: {msg}")


def load(d, ids):
    r = {}
    for f in sorted(Path(d).glob("part.0?.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            x = json.loads(line)
            if x["id"] in r:
                fail(f"{d}: duplicate record for {x['id']}")
            r[x["id"]] = x
    if r.keys() != ids:
        fail(f"{d}: {len(ids - r.keys())} input IDs missing, {len(r.keys() - ids)} not in input")
    for k, x in r.items():
        if "err" in x and x["err"] != "parse":
            fail(f"{d}: {k}: {x['err']}")
        if "err" not in x and not isinstance(x.get("n"), int):
            fail(f"{d}: {k}: no result")
    return r


ids = {line.split("\t", 1)[0] for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()}
o, n = load(sys.argv[2], ids), load(sys.argv[3], ids)
po, pn = ({k for k, x in r.items() if "err" in x} for r in (o, n))
if po != pn:
    fail(f"parse failures differ: {sorted(po ^ pn)}")
print(f"p1_sets.py: {len(ids)} molecules, {len(po)} parse failures in both", file=sys.stderr)
multi = lambda r: {k for k, x in r.items() if x.get("n", 1) > 1}
mo, mn = multi(o), multi(n)
out = {"regression": [[i, n[i]["strings"], n[i]["fix"]] for i in sorted(mn - mo)],
       "fixed": [[i, o[i]["strings"], o[i]["fix"]] for i in sorted(mo - mn)]}
sys.stdout.write(json.dumps(out, indent=0))
both = sorted(mo & mn)
print(f"p1_sets.py: several strings in OLD {len(mo)}, in NEW {len(mn)}, in both {len(both)}", file=sys.stderr)
if len(sys.argv) > 4:
    Path(sys.argv[4]).write_text(json.dumps({"both": [[i, o[i]["strings"], n[i]["strings"]] for i in both]}, indent=0),
                                 encoding="utf-8")
