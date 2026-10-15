"""Historical collection script (network). It documents how the evidence was collected; the supported
operation for this bundle is the offline recompute in RESULT.md. Its download and time limits are not enforced
(see the correction in PROTOCOL.md section 7): run it only under disk, memory and wall-time limits applied
outside the script.

Positive control (PROTOCOL section 5a): plant known defects in copies of one wiki's records and require
the frozen classifier + live confirmation to label every plant correctly.

usage: control.py WIKI   (a current-arm sample wiki whose records are extracted)
Plants, chosen with random.Random(SEED) among pages identical in both files, latest revision before
2026-09-01, page id and title absent from the W recent-changes rows:
  5 pages removed from the export copy      -> expect MISSING_EXPORT / UNEXPLAINED / EXPORT_WRONG
  5 export text hashes altered              -> expect TEXT_DIFF / UNEXPLAINED / EXPORT_WRONG
  2 pages removed from the legacy copy      -> expect MISSING_LEGACY / UNEXPLAINED / LEGACY_WRONG
Pass = 12/12 as expected and no other difference created. Writes evidence/control.json.
"""
from __future__ import annotations

import copy
import json
import random
import sys

from common import EVID, SEED, read_json, read_rc, write_json
from compare import classify, confirm, load

CUTOFF = "2026-09-01T00:00:00Z"


def main(wiki: str) -> int:
    L = load("current", wiki, "legacy")
    E = load("current", wiki, "export")
    L.pop("__dups__", None)
    E.pop("__dups__", None)
    rc = read_rc(wiki)
    t_pid = {r["pageid"] for r in rc["rows"] if r.get("pageid")}
    t_title = {r["title"] for r in rc["rows"] if r.get("title")} | {r["target"] for r in rc["rows"] if r.get("target")}
    base_keys = {d["key"] for d in classify("current", L, E, rc)}
    pool = sorted(k for k in L if k in E and L[k]["rid"] == E[k]["rid"] and L[k]["text_sha1"] == E[k]["text_sha1"]
                  and L[k]["text_sha1"] and (L[k]["ts"] or "") < CUTOFF and k not in t_pid
                  and L[k]["title"] not in t_title and k not in base_keys)
    picks = random.Random(SEED).sample(pool, 12)
    drop_e, alter_e, drop_l = picks[:5], picks[5:10], picks[10:]
    L2, E2 = dict(L), dict(E)
    for k in drop_e:
        del E2[k]
    for k in alter_e:
        E2[k] = copy.deepcopy(E[k])
        E2[k]["text_sha1"] = "0" * 40
    for k in drop_l:
        del L2[k]
    diffs = [d for d in classify("current", L2, E2, rc) if d["key"] not in base_keys]
    confirm("current", wiki, diffs)
    expect = {**{k: ("MISSING_EXPORT", "EXPORT_WRONG") for k in drop_e},
              **{k: ("TEXT_DIFF", "EXPORT_WRONG") for k in alter_e},
              **{k: ("MISSING_LEGACY", "LEGACY_WRONG") for k in drop_l}}
    got = {d["key"]: (d["type"], d["class"], d["live"]["verdict"]) for d in diffs}
    ok = [k for k, (t, v) in expect.items() if got.get(k) == (t, "UNEXPLAINED", v)]
    extra = sorted(set(got) - set(expect))
    out = {"wiki": wiki, "pool": len(pool), "planted": len(expect), "correct": len(ok), "extra_diffs": extra,
           "pass": len(ok) == len(expect) and not extra,
           "detail": {str(k): {"expect": expect[k], "got": got.get(k)} for k in expect}}
    write_json(EVID / "control.json", out)
    print(json.dumps({k: out[k] for k in ("wiki", "pool", "planted", "correct", "extra_diffs", "pass")}))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
