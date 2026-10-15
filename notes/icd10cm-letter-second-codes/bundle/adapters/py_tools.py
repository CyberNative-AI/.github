"""Python adapters: one documented validity/lookup call per tool. Usage: py_tools.py PROBES OUTDIR"""
import json, sys, traceback
from datetime import date
from pathlib import Path

probes = [json.loads(l) for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()]
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)

def t_simple():
    import simple_icd_10_cm as m
    return "simple-icd-10-cm 1.5.0 is_valid_item(dotted)", lambda p: (m.is_valid_item(p["dotted"]), None)

def t_icdlookup():
    from icdlookup import lookup
    def f(p):
        r = lookup(p["dotted"]); return r is not None, r
    return "icdlookup 0.1.0 lookup(dotted)", f

def t_cmsicd():
    from cms_icd import ICD10KnowledgeBase
    kb = ICD10KnowledgeBase.for_date(date(2026, 10, 14))
    def f(p):
        try:
            c = kb.cm[p["dotted"]]
            return True, getattr(c, "description", str(c))
        except KeyError as e:
            return False, "KeyError:" + str(e)[:120]
    return "cms-icd 0.3.1 ICD10KnowledgeBase.for_date(2026-10-14).cm[dotted]", f

def t_coder():
    from icd10_coder import coder
    return "icd10-coder 0.2.3 _code_exists('cm', undotted) (used by its `code` command)", lambda p: (coder._code_exists("cm", p["code"]), None)

TOOLS = {"simple-icd-10-cm": t_simple, "icdlookup": t_icdlookup, "cms-icd": t_cmsicd, "icd10-coder": t_coder}
only = sys.argv[3:] or list(TOOLS)
for name in only:
    rows = []
    try:
        call, fn = TOOLS[name]()
    except Exception:
        (out / f"{name}.jsonl").write_text(json.dumps({"tool": name, "setup_error": traceback.format_exc()[-800:]}) + "\n"); continue
    for p in probes:
        try:
            ok, raw = fn(p); err = None
        except Exception as e:
            ok, raw, err = False, None, f"{type(e).__name__}: {str(e)[:200]}"
        rows.append({"tool": name, "call": call, "arm": p["arm"], "code": p["code"], "accept": bool(ok),
                     "raw": None if raw is None else str(raw)[:160], "error": err})
    (out / f"{name}.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    print(name, sum(r["accept"] for r in rows), "/", len(rows))
