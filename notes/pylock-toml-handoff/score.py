"""Score install cells. Usage: python3 score.py RESULTS_DIR LABEL [LABEL ...] > out.json

Labels per PROTOCOL.md. Single-use selections (S0-S2) compare against the producer's native
install on the same target; multi-use (M) cells compare against the spec oracle only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load(d: Path):
    cells = [json.loads(x) for x in (d / "cells.jsonl").read_text(encoding="utf-8").splitlines()]
    orc = [json.loads(x) for x in (d / "oracle.jsonl").read_text(encoding="utf-8").splitlines()]
    return cells, {(o["lock"], o["consume_sel"]): o for o in orc}


def diff(a: dict | None, b: dict | None) -> dict:
    a, b = a or {}, b or {}
    return {
        "missing": sorted(k for k in b if k not in a),
        "extra": sorted(k for k in a if k not in b),
        "version": sorted(f"{k}:{a[k]}!={b[k]}" for k in a if k in b and b[k] is not None and a[k] != b[k]),
    }


def empty(dd: dict) -> bool:
    return not (dd["missing"] or dd["extra"] or dd["version"])


def score(label: str, root: Path) -> list[dict]:
    cells, orc = load(root / label)
    native = {(c["producer"], c["sel"]): c for c in cells if c.get("kind") == "native"}
    out = []
    for c in cells:
        if c.get("kind") not in ("pylock", "req"):
            continue
        row = {k: c[k] for k in ("cell", "producer", "sel", "kind", "consumer", "consume_sel", "rc")}
        row["target"] = label
        o = orc.get((f"{c['producer']}/{c['sel']}", c["consume_sel"])) if c["kind"] == "pylock" else None
        ok_run = c["rc"] == 0
        if c["sel"] != "M":
            n = native[(c["producer"], c["sel"])]
            row["native_rc"] = n["rc"]
            if n["rc"] != 0:
                row["label"] = "OK" if not ok_run else "SILENT_WRONG"
                row["why"] = "native refuses; consumer " + ("refuses" if not ok_run else "installs")
            elif not ok_run:
                row["label"] = "LOUD"
            else:
                dd = diff(c["installed"], n["installed"])
                row["label"] = "OK" if empty(dd) else "SILENT_WRONG"
                row["vs_native"] = dd
        else:
            if o is None:
                row["label"] = "NO_ORACLE"
            elif o["refuse"]:
                row["label"] = "OK" if not ok_run else "SILENT_WRONG"
                row["why"] = f"oracle refuses ({','.join(o['refuse'])})"
            elif not ok_run:
                row["label"] = "LOUD"
            else:
                dd = diff(c["installed"], o["set"])
                row["label"] = "OK" if empty(dd) else "SILENT_WRONG"
                row["vs_oracle"] = dd
        if o is not None:
            if c["sel"] != "M":
                n = native[(c["producer"], c["sel"])]
                if n["rc"] == 0 and not o["refuse"]:
                    row["producer_side"] = diff(o["set"], n["installed"])
                elif n["rc"] != 0:
                    row["producer_side"] = {"oracle_refuses": o["refuse"], "native_refuses": True}
            if ok_run and not o["refuse"]:
                row["consumer_side"] = diff(c["installed"], o["set"])
            elif ok_run and o["refuse"]:
                row["consumer_side"] = {"installed_despite_oracle_refusal": o["refuse"]}
        if not ok_run:
            row["tail"] = c.get("tail", "")[-400:]
        out.append(row)
    return out


if __name__ == "__main__":
    root = Path(sys.argv[1])
    rows = []
    for lab in sys.argv[2:]:
        rows.extend(score(lab, root))
    json.dump(rows, sys.stdout, indent=1, sort_keys=True)
