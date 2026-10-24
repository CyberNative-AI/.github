"""Tally census.py output. usage: analyse.py census.jsonl"""
import json, sys, collections
rows = [json.loads(l) for l in open(sys.argv[1])]
OK = [r for r in rows if "hits" in r]; c = collections.Counter(); out = []
O_KEYS = ("O_MAN", "R_MAN", "O_CODE", "O_DART", "O_CDV", "O_EXPO")
for r in OK:
    h = r["hits"]; ht = r["head_target"]; low = ht is None or ht <= 35
    E = bool(h["E"]); O = any(h[k] for k in O_KEYS); opt = bool(h["OPT_R"]); game = bool(h["GAME"])
    ar_e = low and E; ar_o = low and O and not opt and not game; dead_e = (ht is not None and ht >= 36) and E
    c["scanned"] += 1; c["head<=35"] += ht is not None and ht <= 35; c["unresolved"] += ht is None; c["head>=36"] += ht is not None and ht >= 36
    c["E"] += E; c["O_any"] += O; c["OPT_R"] += opt; c["GAME"] += game
    for k in O_KEYS: c[k] += bool(h[k])
    c["AT_RISK_E"] += ar_e; c["AT_RISK_O"] += ar_o; c["DEAD_E"] += dead_e; c["AT_RISK_E|O"] += ar_e or ar_o
    c["O_with_head>=36"] += O and ht is not None and ht >= 36 and not opt and not game
    if E or O or opt or game: out.append({"pkg": r["pkg"], "head_target": ht, "AT_RISK_E": ar_e, "AT_RISK_O": ar_o, "DEAD_E": dead_e,
        "hits": {k: v for k, v in h.items() if v}})
c["errors"] = len(rows) - len(OK); c["rows"] = len(rows)
print(json.dumps({"counts": dict(sorted(c.items())), "rows": out}, indent=1))
