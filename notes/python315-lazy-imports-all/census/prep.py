"""Derive import names per installed project from its own dist-info RECORD. Outcome-blind.

Usage (inside container): python prep.py /w/envs /w/install OUT.json
"""
import csv
import json
import re
import sys
from pathlib import Path

SKIP_TOP = {"tests", "test", "testing", "docs", "examples", "benchmarks", "bin", "scripts"}


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def import_names(record_rows):
    paths = [r[0] for r in record_rows if r]
    paths = [p for p in paths if not p.startswith("..") and ".dist-info/" not in p and ".data/" not in p
             and "__pycache__" not in p]
    pkgs = set()
    mods = set()
    for p in paths:
        parts = p.split("/")
        if parts[0] in SKIP_TOP:
            continue
        if parts[-1] == "__init__.py":
            pkgs.add(".".join(parts[:-1]))
        elif len(parts) == 1 and (p.endswith(".py") or p.endswith(".so")):
            mods.add(parts[0].split(".")[0])
    # minimal regular packages: no ancestor is itself a regular package of this dist
    minimal = set()
    for pk in pkgs:
        segs = pk.split(".")
        if not any(".".join(segs[:i]) in pkgs for i in range(1, len(segs))):
            minimal.add(pk)
    names = sorted(n for n in minimal | mods if n and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", n))
    return names


def main():
    envs, inst, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    units = []
    for rcf in sorted(inst.glob("*.rc")):
        p = rcf.stem
        rc = int(rcf.read_text().strip() or "-1")
        u = {"project": p, "install_rc": rc, "names": [], "dist_version": None}
        if rc == 0:
            sp = next((envs / p / "lib").glob("python3.15/site-packages"), None)
            for di in sorted(sp.glob("*.dist-info")) if sp else []:
                stem = di.name[:-len(".dist-info")]
                dname, _, dver = stem.rpartition("-")
                if norm(dname) == norm(p):
                    u["dist_version"] = dver
                    with open(di / "RECORD", newline="", encoding="utf-8") as fh:
                        u["names"] = import_names(list(csv.reader(fh)))[:10]
        units.append(u)
    out.write_text(json.dumps(units, indent=1, sort_keys=True) + "\n", encoding="utf-8")


main()
