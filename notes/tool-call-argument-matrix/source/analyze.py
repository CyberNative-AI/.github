"""Frozen classification and decision for the tool-call argument matrix. usage: python analyze.py <out_dir>"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ERR_RE = re.compile(r"(?i)(error|invalid|json|pars|decod|expect|malformed|validat|fail)")
INTENDED = {"list_items": {"status": "archived"}, "get_weather": {"city": "Paris"}}
TARGET = {"r_trunc": "get_weather"}
CORE = ["v_trunc", "v_extra_brace"]
ALLV = CORE + ["v_single_quote", "v_double_enc", "v_fenced", "r_trunc"]
REPORT_ONLY = ["v_empty"]  # "" -> {} is a defensible convention; reported, not counted
SILENT = {"SILENT_WRONG", "DROP_SILENT"}


def load(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def returned_text(reqs: list[dict]) -> str:
    """Text the framework sent back to the model after the first tool call (seq >= 2)."""
    out = []
    for r in reqs:
        if r["seq"] < 2:
            continue
        msgs = r["body"].get("messages") or []
        seen_call = False
        for m in msgs:
            if m.get("role") == "assistant" and m.get("tool_calls"):
                seen_call = True
                continue
            if seen_call and m.get("role") in ("tool", "user", "system"):
                c = m.get("content")
                out.append(c if isinstance(c, str) else json.dumps(c))
    return "\n".join(out)


def classify(cell: dict, tools: list[dict], reqs: list[dict]) -> str:
    target = TARGET.get(cell["scenario"], "list_items")
    calls = [t for t in tools if t["tool"] == target]
    res = cell.get("result") or {}
    if calls:
        if all(c["kwargs"] == INTENDED[target] for c in calls):
            return "EXEC_INTENDED"
        return "SILENT_WRONG" if cell["scenario"] != "ctl_empty_obj" else "EXEC_DEFAULT"
    if res.get("outcome") == "exception":
        return "RAISE"
    if ERR_RE.search(returned_text(reqs)):
        return "MODEL_ERROR"
    if res.get("outcome") == "final" and ERR_RE.search(res.get("message") or ""):
        return "CALLER_ERROR"
    if res.get("outcome") == "final":
        return "DROP_SILENT"
    return "OTHER"


def main() -> None:
    out = Path(sys.argv[1])
    cells = load(out / "cells.jsonl")
    tools = defaultdict(list)
    for t in load(out / "tools.jsonl"):
        tools[t["run_id"]].append(t)
    reqs = defaultdict(list)
    for r in load(out / "requests.jsonl"):
        reqs[r["run_id"]].append(r)
    grid: dict = defaultdict(dict)
    rows = []
    for c in cells:
        cls = classify(c, tools[c["run_id"]], sorted(reqs[c["run_id"]], key=lambda r: r["seq"]))
        grid[(c["framework"], c["scenario"])].setdefault("reps", []).append(cls)
        rows.append({"run_id": c["run_id"], "class": cls, "n_requests": len(reqs[c["run_id"]]),
                     "tool_kwargs": [t["kwargs"] for t in tools[c["run_id"]]],
                     "stream": sorted({bool(r["body"].get("stream")) for r in reqs[c["run_id"]]}),
                     "result": c.get("result"), "returned_text": returned_text(sorted(reqs[c["run_id"]], key=lambda r: r["seq"]))[:300]})
    fws = sorted({c["framework"] for c in cells})

    def stable(fw, sc):
        reps = grid.get((fw, sc), {}).get("reps", [])
        return reps[0] if reps and len(set(reps)) == 1 else ("UNSTABLE" if reps else "MISSING")

    valid = [fw for fw in fws if stable(fw, "ctl_valid") == "EXEC_INTENDED"]
    s_core = [fw for fw in valid if any(stable(fw, v) in SILENT for v in CORE)]
    s_any = [fw for fw in valid if any(stable(fw, v) in SILENT for v in ALLV)]
    if len(valid) < 6:
        decision = "INVALID"
    elif len(s_core) >= 3:
        decision = "CONTINUE"
    elif len(s_any) >= 3:
        decision = "CHANGE"
    else:
        decision = "STOP"
    matrix = {fw: {sc: stable(fw, sc) for sc in ["ctl_valid", "ctl_empty_obj"] + ALLV + REPORT_ONLY} for fw in fws}
    res = {"decision": decision, "valid_frameworks": valid, "silent_core": s_core, "silent_any": s_any,
           "excluded": [fw for fw in fws if fw not in valid], "matrix": matrix}
    (out / "results.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (out / "cells-classified.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("decision", "valid_frameworks", "silent_core", "silent_any", "excluded")}, indent=1))
    for fw in fws:
        print(f"{fw:15s}", " ".join(f"{sc}={matrix[fw][sc]}" for sc in matrix[fw]))


if __name__ == "__main__":
    main()
