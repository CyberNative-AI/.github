"""Classify each unit from walk outputs (frozen rules in PROTOCOL.md). Host Python, stdlib only.

Usage: python analyze.py W_DIR UNITS.json OUT_DIR OUT_JSON [--arm-f OUT_DIR_F]
"""
import csv
import json
import re
import sys
from pathlib import Path

CALIBRATION = {"six", "pandas", "polars", "sqlalchemy", "orjson", "pydantic", "google-cloud-storage", "numpy"}
SP = "/lib/python3.15/site-packages/"


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def owner_map(env):
    """relative path inside site-packages -> normalized dist name, from every RECORD in the env."""
    m = {}
    sp = env / "lib/python3.15/site-packages"
    for di in sorted(sp.glob("*.dist-info")) if sp.exists() else []:
        dname = di.name[:-len(".dist-info")].rpartition("-")[0]
        rec = di / "RECORD"
        if not rec.exists():
            continue
        with open(rec, newline="", encoding="utf-8") as fh:
            for row in csv.reader(fh):
                if row:
                    m[row[0]] = norm(dname)
    return m


def owner_of(path, omap):
    if not path:
        return "cpython"
    if path.startswith("/ctl/"):
        return "ctl"
    if SP in path:
        rel = path.split(SP, 1)[1]
        return omap.get(rel, "unknown-site-packages")
    return "cpython"


def under(mod, prefixes):
    return any(mod == p or mod.startswith(p + ".") for p in prefixes)


def load(outdir, project, arm, rep):
    f = outdir / f"{project}__{arm}__{rep}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def status(rec):
    if rec is None:
        return "MISSING"
    if rec["rc"] == "TIMEOUT":
        return "TIMEOUT"
    if rec["rc"] != 0 or not rec.get("result"):
        return "FAIL"
    if not rec["result"].get("walk_complete"):
        return "INCOMPLETE"
    return "OK"


def keys(rec, names, dropped):
    res = rec["result"]
    k = {}
    for n in names:
        imp = res["imports"].get(n, {})
        if not imp.get("ok", False):
            k[("import", n, imp.get("type"))] = imp
    for e in res["walk_errors"]:
        if under(e["module"], dropped):
            continue
        k[("walk", e["module"], e["attr"], e["type"])] = e
    return k


def classify(u, outdir, envs, arm_b="all"):
    p = u["project"]
    recs = {(a, r): load(outdir, p, a, r) for a in ("normal", arm_b) for r in (1, 2)}
    st = {f"{a}{r}": status(v) for (a, r), v in recs.items()}
    out = {"project": p, "dist_version": u.get("dist_version"), "names": u["names"], "status": st,
           "calibration": p in CALIBRATION}
    if any(st[f"normal{r}"] != "OK" for r in (1, 2)):
        out["class"] = "EXCLUDED_NORMAL_" + "/".join(sorted({st["normal1"], st["normal2"]}))
        return out
    elig = [n for n in u["names"] if all(recs[("normal", r)]["result"]["imports"].get(n, {}).get("ok") for r in (1, 2))]
    dropped = [n for n in u["names"] if n not in elig]
    out["eligible_names"], out["dropped_names"] = elig, dropped
    if not elig:
        out["class"] = "EXCLUDED_NO_IMPORT"
        return out
    bst = [st[f"{arm_b}1"], st[f"{arm_b}2"]]
    if any(s in ("FAIL", "TIMEOUT", "MISSING") for s in bst):
        out["class"] = "BREAK_CRASH" if all(s in ("FAIL", "TIMEOUT") for s in bst) else "UNSTABLE_CRASH"
        out["b_stderr"] = (recs[(arm_b, 1)] or {}).get("stderr_tail", "")[-600:]
        out["attribution"] = "UNATTRIBUTED"
        return out
    kn1, kn2 = keys(recs[("normal", 1)], elig, dropped), keys(recs[("normal", 2)], elig, dropped)
    kb1, kb2 = keys(recs[(arm_b, 1)], elig, dropped), keys(recs[(arm_b, 2)], elig, dropped)
    extra = (set(kb1) & set(kb2)) - (set(kn1) | set(kn2))
    unstable = (set(kb1) ^ set(kb2)) | (set(kn1) ^ set(kn2))
    out["n_extra"], out["n_unstable"] = len(extra), len(unstable)
    omap = owner_map(envs / p) if p and not p.startswith("ctl-") else {}
    owners = {}
    for k in sorted(extra):
        e = kb1[k]
        o = owner_of(e.get("deepest_site_packages", ""), omap)
        owners[o] = owners.get(o, 0) + 1
    out["owners"] = owners
    ex = sorted(extra)
    out["examples"] = [dict(key=list(k), msg=kb1[k].get("msg", "")[:200],
                            frame=kb1[k].get("deepest_site_packages") or kb1[k].get("deepest")) for k in ex[:5]]
    out["top_level_attrs_affected"] = sorted({k[2] for k in extra if k[0] == "walk" and k[1] in elig})[:50]
    out["n_top_level_attrs_affected"] = len({k[2] for k in extra if k[0] == "walk" and k[1] in elig})
    if st[f"{arm_b}1"] == "INCOMPLETE" or st[f"{arm_b}2"] == "INCOMPLETE":
        out["b_incomplete"] = True
    nset = set(recs[("normal", 1)]["result"]["modules_after"])
    bset = set(recs[(arm_b, 1)]["result"]["modules_after"])
    out["modules_only_normal"] = sorted(m for m in nset - bset if not under(m, dropped))[:40]
    out["n_modules_only_normal"] = len([m for m in nset - bset if not under(m, dropped)])
    if extra:
        out["class"] = "BREAK_IMPORT" if any(k[0] == "import" for k in extra) else "BREAK_REIFY"
        own = norm(p) if not p.startswith("ctl-") else "ctl"
        out["attribution"] = "OWN" if own in owners else ("DEP" if any(o not in ("cpython",) for o in owners) else "CPYTHON")
    elif unstable:
        out["class"] = "UNSTABLE"
    else:
        out["class"] = "OK"
    return out


def main():
    w = Path(sys.argv[1])
    units = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    outdir = Path(sys.argv[3])
    arm_b = "deny" if "--arm-f" in sys.argv else "all"
    rows = [classify(u, outdir, w / "envs", arm_b) for u in units if u.get("names")]
    rows += [{"project": u["project"], "class": "EXCLUDED_INSTALL" if u["install_rc"] != 0 else "EXCLUDED_NO_NAMES",
              "install_rc": u["install_rc"], "calibration": u["project"] in CALIBRATION}
             for u in units if not u.get("names")]
    Path(sys.argv[4]).write_text(json.dumps(sorted(rows, key=lambda r: r["project"]), indent=1, sort_keys=True) + "\n",
                                 encoding="utf-8")
    tally = {}
    for r in rows:
        key = (r["class"], r.get("attribution", "-"), "cal" if r["calibration"] else "frame")
        tally[key] = tally.get(key, 0) + 1
    for k in sorted(tally):
        print(*k, tally[k], sep="\t")


main()
