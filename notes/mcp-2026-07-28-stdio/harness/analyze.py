"""Apply the mcp-stdio-cross-era frozen decision rule (PROTOCOL.md "Measures"/"Controls"/"Decision rule").

usage: python3 analyze.py CONFIG.json RESULTS_DIR > RESULT.json
RESULTS_DIR: cells.jsonl (tags classify/main/descriptive/notap), tap/, probes/<server>.json,
client_era.json (written by `classify` mode before the main run), KNOWN-adjudication.json (optional).

python3 analyze.py --classify CONFIG.json RESULTS_DIR   -> writes RESULTS_DIR/client_era.json
"""

import json
import os
import re
import statistics
import sys
from collections import defaultdict

SPEC = {  # (client era, server era) -> spec outcome (versioning.md Compatibility Matrix)
    ("MODERN_ONLY", "MODERN_ONLY"): "Works", ("MODERN_ONLY", "DUAL"): "Works", ("MODERN_ONLY", "LEGACY_ONLY"): "Fails",
    ("DUAL", "MODERN_ONLY"): "Works", ("DUAL", "DUAL"): "Works", ("DUAL", "LEGACY_ONLY"): "Works",
    ("LEGACY", "MODERN_ONLY"): "Fails", ("LEGACY", "DUAL"): "Works", ("LEGACY", "LEGACY_ONLY"): "Works",
}
SERVER_UPGRADES = [
    ("py-mcp-1.30.0", "py-mcp-2.3.0"), ("py-fastmcp-3.4.8", "py-fastmcp-4.1.0"), ("ts-sdk-1.32.1", "ts-v2-2.3.1"),
    ("go-sdk-1.6.1", "go-sdk-1.8.0"), ("mcp-go-0.57.0", "mcp-go-1.2.1"),
    ("everything-2026.7.4", "everything-1.0.0"), ("filesystem-2026.7.4", "filesystem-1.0.0"),
]
CLIENT_UPGRADES = SERVER_UPGRADES[:5]
VERSION_RX = re.compile(r"20\d\d-\d\d-\d\d|protocol version", re.I)


def load(rd):
    return [json.loads(l) for l in open(os.path.join(rd, "cells.jsonl"), encoding="utf-8")]


def tap_methods(rd, r):
    path = os.path.join(rd, "tap", "%s__%s__%s__%d.jsonl" % (r["tag"], r["client"], r["server"], r["rep"]))
    out = []
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            x = json.loads(ln)
            if x["dir"] == "c2s":
                try:
                    m = json.loads(x["line"]).get("method")
                except (ValueError, AttributeError):
                    m = None
                if m:
                    out.append((x["t_ms"], m))
    return out


def run_outcome(r, srv):
    if r.get("hard_timeout"):
        return "FAIL"
    res = r.get("result")
    if res is None:
        return "HARNESS"
    ok = bool(res.get("connect_ok") and res.get("list_ok") and res.get("call_ok"))
    ok = ok and srv.get("tool", "echo") in (res.get("tools") or []) and not res.get("call_is_error")
    exp = srv.get("expect", "echo:hello-re13340")
    if exp is not None:
        ok = ok and exp in (res.get("call_text") or "")
    return "PASS" if ok else "FAIL"


def classify(cfg, rd):
    recs = [r for r in load(rd) if r["tag"] == "classify"]
    era = {}
    for c in cfg["clients"]:
        rs = [r for r in recs if r["client"] == c and r["server"] == "fake-legacy_32602"]
        seqs = [[m for _, m in tap_methods(rd, r)] for r in rs]
        firsts = {s[0] for s in seqs if s}
        if not firsts:
            era[c] = None
        elif firsts == {"initialize"}:
            era[c] = "LEGACY"
        elif firsts == {"server/discover"}:
            era[c] = "DUAL" if all("initialize" in s for s in seqs) else "MODERN_ONLY" if not any("initialize" in s for s in seqs) else "MIXED"
        else:
            era[c] = "MIXED"
    json.dump({"client_era": era, "basis": "first method + initialize-after-discover against fake-legacy_32602, tag classify"},
              open(os.path.join(rd, "client_era.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps(era, indent=1, sort_keys=True))


def main():
    if sys.argv[1] == "--classify":
        return classify(json.load(open(sys.argv[2])), sys.argv[3])
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    rd = sys.argv[2]
    recs = load(rd)
    cli_era = json.load(open(os.path.join(rd, "client_era.json")))["client_era"]
    srv_era = {}
    for s in cfg["servers"]:
        p = os.path.join(rd, "probes", s + ".json")
        srv_era[s] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
    era_of = {s: (v or {}).get("era") for s, v in srv_era.items()}
    by = defaultdict(list)
    for r in recs:
        srv = cfg["servers"][r["server"]]
        r["_o"] = run_outcome(r, srv)
        tm = tap_methods(rd, r)
        r["_methods"] = [m for _, m in tm]
        d = [t for t, m in tm if m == "server/discover"]
        i = [t for t, m in tm if m == "initialize"]
        r["_gap"] = (i[0] - d[0]) if d and i and i[0] > d[0] else None
        by[(r["tag"], r["client"], r["server"])].append(r)

    def cell(tag, c, s):
        rs = by.get((tag, c, s), [])
        os_ = [r["_o"] for r in rs if r["_o"] != "HARNESS"]
        v = "PASS" if os_.count("PASS") >= 2 else "FAIL" if os_.count("FAIL") >= 2 else "FLAKY" if rs else None
        tcs = [(r.get("result") or {}).get("t_connect_ms") for r in rs]
        tcs = [t for t in tcs if isinstance(t, (int, float))]
        gaps = [r["_gap"] for r in rs if r["_gap"] is not None]
        errs = sorted({"%s%s: %s" % ("TIMEOUT " if r.get("hard_timeout") else "", (r.get("result") or {}).get("error_stage") or "",
                                       ((r.get("result") or {}).get("error_msg") or "")[:300]) for r in rs if r["_o"] != "PASS"})
        return {"client": c, "server": s, "client_era": cli_era.get(c), "server_era": era_of.get(s),
                "spec": SPEC.get((cli_era.get(c), era_of.get(s))), "verdict": v, "runs": [r["_o"] for r in rs],
                "t_connect_median_ms": statistics.median(tcs) if tcs else None,
                "fallback_gap_median_ms": statistics.median(gaps) if gaps else None,
                "methods_first_run": rs[0]["_methods"][:6] if rs else None, "errors": errs}

    clients = sorted(cfg["clients"])
    real = sorted(s for s, v in cfg["servers"].items() if v.get("real"))
    fakes = sorted(s for s, v in cfg["servers"].items() if not v.get("real"))
    main_cells = {(c, s): cell("main", c, s) for c in clients for s in real}
    desc_cells = {(c, s): cell("descriptive", c, s) for c in clients for s in fakes}
    croot = cfg["client_root"]
    sroot = {s: v["root"] for s, v in cfg["servers"].items()}

    D = []
    for (c, s), x in sorted(main_cells.items()):
        cross = not (x["client_era"] == "LEGACY" and x["server_era"] == "LEGACY_ONLY")
        if cross and x["spec"] == "Works" and x["verdict"] == "FAIL":
            D.append({"kind": "F", "client": c, "server_root": sroot[s], "server": s, "root": croot[c], "errors": x["errors"]})
    # merge F to distinct (client, server root)
    seen, F = set(), []
    for it in D:
        k = (it["client"], it["server_root"])
        if k in seen:
            next(f for f in F if (f["client"], f["server_root"]) == k)["servers"].append(it["server"])
            continue
        seen.add(k)
        F.append({"kind": "F", "client": it["client"], "server_root": it["server_root"], "servers": [it["server"]], "root": it["root"], "errors": it["errors"]})
    legacy_clients = [c for c in clients if cli_era.get(c) == "LEGACY"]
    U = []
    for old, new in SERVER_UPGRADES:
        broken = [lc for lc in legacy_clients if main_cells[(lc, old)]["verdict"] == "PASS" and main_cells[(lc, new)]["verdict"] == "FAIL"]
        if broken:
            U.append({"kind": "U", "line": [old, new], "root": sroot[new], "legacy_clients_broken": broken,
                      "spec": sorted({main_cells[(lc, new)]["spec"] or "?" for lc in broken}),
                      "diagnostic_names_version": {lc: any(VERSION_RX.search(e) for e in main_cells[(lc, new)]["errors"]) for lc in broken},
                      "errors": {lc: main_cells[(lc, new)]["errors"] for lc in broken}})
    Uc = []
    for old, new in CLIENT_UPGRADES:
        broken = [s for s in real if main_cells[(old, s)]["verdict"] == "PASS" and main_cells[(new, s)]["verdict"] == "FAIL"]
        if broken:
            Uc.append({"kind": "Uc", "line": [old, new], "root": croot[new], "servers_broken": broken,
                       "spec": sorted({main_cells[(new, s)]["spec"] or "?" for s in broken}),
                       "errors": {s: main_cells[(new, s)]["errors"] for s in broken}})
    items = F + U + Uc
    slow = [x for x in main_cells.values() if x["spec"] == "Works" and x["verdict"] == "PASS"
            and x["fallback_gap_median_ms"] is not None and x["fallback_gap_median_ms"] >= 1000]

    # controls
    ctrl = {}
    ctrl["self_cells"] = {c: [r["_o"] for r in by.get(("main", c, s), [])] for c, s in cfg["self_cells"].items()}
    ctrl["self_ok"] = all(v.count("PASS") == 3 for v in ctrl["self_cells"].values())
    want = {"fake-modern": "MODERN_ONLY", "fake-dual": "DUAL", "fake-legacy_32602": "LEGACY_ONLY", "py-mcp-1.12.4": "LEGACY_ONLY"}
    ctrl["probe_controls"] = {s: era_of.get(s) for s in want}
    ctrl["probe_ok"] = all(era_of.get(s) == e for s, e in want.items())
    tr = {}
    for c, s in cfg["transparency"].items():
        a = [r for r in by.get(("notap", c, s), [])]
        b = [r for r in by.get(("main", c, s), [])]
        ta = [(r.get("result") or {}).get("t_connect_ms") for r in a]
        tb = [(r.get("result") or {}).get("t_connect_ms") for r in b]
        ta, tb = [t for t in ta if t is not None], [t for t in tb if t is not None]
        same = [r["_o"] for r in a] == ["PASS"] * 3 and [r["_o"] for r in b] == ["PASS"] * 3
        dt = abs(statistics.median(ta) - statistics.median(tb)) if ta and tb else None
        tr[c] = {"outcomes_notap": [r["_o"] for r in a], "outcomes_tap": [r["_o"] for r in b], "dt_median_ms": dt, "ok": same and dt is not None and dt <= 200}
    ctrl["transparency"] = tr
    ctrl["transparency_ok"] = bool(tr) and all(v["ok"] for v in tr.values())
    mains = [r for r in recs if r["tag"] == "main"]
    nh = sum(r["_o"] == "HARNESS" for r in mains)
    per = defaultdict(lambda: [0, 0])
    for r in mains:
        per[r["client"]][0] += r["_o"] == "HARNESS"
        per[r["client"]][1] += 1
    ctrl["harness_rate"] = nh / len(mains) if mains else None
    ctrl["harness_max_client_rate"] = max((h / n for h, n in per.values()), default=None)
    ctrl["harness_ok"] = mains != [] and ctrl["harness_rate"] <= 0.02 and ctrl["harness_max_client_rate"] <= 0.10
    valid = ctrl["self_ok"] and ctrl["probe_ok"] and ctrl["transparency_ok"] and ctrl["harness_ok"]

    adj_path = os.path.join(rd, "KNOWN-adjudication.json")
    adj = json.load(open(adj_path)) if os.path.exists(adj_path) else {}
    for it in items:
        key = "%s|%s|%s" % (it["kind"], it.get("client") or "->".join(it["line"]), it.get("server_root", ""))
        it["key"] = key
        it["known"] = adj.get(key)
    roots = {it["root"] for it in items}
    new_items = [it for it in items if it["known"] is not None and not it["known"].get("known")]
    unadjudicated = [it["key"] for it in items if it["known"] is None]
    if not valid:
        ruling = "INVALID"
    elif unadjudicated:
        ruling = "PENDING_ADJUDICATION"
    elif len(items) >= 2 and len(roots) >= 2 and new_items:
        ruling = "CONTINUE"
    elif items or slow:
        ruling = "CHANGE"
    else:
        ruling = "STOP"
    out = {"ruling": ruling, "n_items": len(items), "roots": sorted(roots), "n_new": len(new_items), "unadjudicated": unadjudicated,
           "items": items, "SLOW": [{k: x[k] for k in ("client", "server", "fallback_gap_median_ms")} for x in slow],
           "controls": ctrl, "client_era": cli_era, "server_era": era_of,
           "server_discover_shape": {s: (v or {}).get("discover_shape") for s, v in srv_era.items()},
           "baseline_legacy_legacy_fails": [{k: x[k] for k in ("client", "server", "runs", "errors")} for x in main_cells.values()
                                            if x["client_era"] == "LEGACY" and x["server_era"] == "LEGACY_ONLY" and x["verdict"] != "PASS"],
           "n_main_runs": len(mains), "main_cells": list(main_cells.values()), "descriptive_cells": list(desc_cells.values())}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
