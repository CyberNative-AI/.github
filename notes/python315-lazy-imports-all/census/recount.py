"""Independent recount of the census classes from the raw runs, written from the method
text in ../README.md (does not import or copy analyze.py).

    mkdir raw && tar xzf raw-runs.tar.gz -C raw && python -I recount.py raw
    python -I recount.py holdout/h --fix-arm eco --no-calibration   # ranks 301-500
"""
import json, sys
from collections import Counter
from pathlib import Path

root = Path(sys.argv[1])
FIX_ARM = sys.argv[sys.argv.index("--fix-arm") + 1] if "--fix-arm" in sys.argv else "deny"
units = json.loads((root / "units.json").read_text())
CAL = set() if "--no-calibration" in sys.argv else {
    "six", "pandas", "polars", "sqlalchemy", "orjson", "pydantic", "google-cloud-storage", "numpy"}


def load(p, arm, rep):
    f = root / "out" / f"{p}__{arm}__{rep}.json"
    return json.loads(f.read_text()) if f.exists() else None


def ok_run(r):
    return r is not None and r.get("rc") == 0 and isinstance(r.get("result"), dict) and r["result"].get("walk_complete") is True


def under(mod, names):
    return any(mod == n or mod.startswith(n + ".") for n in names)


def keys(r, eligible, dropped):
    out = set()
    if r is None or not isinstance(r.get("result"), dict):
        return out
    res = r["result"]
    for n, v in res.get("imports", {}).items():
        if n in eligible and not v.get("ok"):
            out.add(("import", n, v.get("type")))
    for e in res.get("walk_errors", []):
        if dropped and under(e["module"], dropped):
            continue
        out.add(("walk", e["module"], e["attr"], e["type"]))
    return out


classes, extras = {}, {}
for u in units:
    p, names = u["project"], u["names"]
    if u["install_rc"] != 0:
        classes[p] = "EXCLUDED_INSTALL"; continue
    if not names:
        classes[p] = "EXCLUDED_NO_NAMES"; continue
    n1, n2 = load(p, "normal", 1), load(p, "normal", 2)
    if not (ok_run(n1) and ok_run(n2)):
        classes[p] = "EXCLUDED_NORMAL"; continue
    elig = [n for n in names if n1["result"]["imports"].get(n, {}).get("ok") and n2["result"]["imports"].get(n, {}).get("ok")]
    dropped = [n for n in names if n not in elig]
    if not elig:
        classes[p] = "EXCLUDED_NO_IMPORT"; continue
    a1, a2 = load(p, "all", 1), load(p, "all", 2)
    kn = keys(n1, elig, dropped) | keys(n2, elig, dropped)
    k1, k2 = keys(a1, elig, dropped), keys(a2, elig, dropped)
    extra = (k1 & k2) - kn
    crash = lambda r: r is None or r.get("rc") != 0 or not isinstance(r.get("result"), dict)
    if crash(a1) and crash(a2):
        c = "BREAK_CRASH"
    elif any(k[0] == "import" for k in extra):
        c = "BREAK_IMPORT"
    elif extra:
        c = "BREAK_REIFY"
    elif k1 != k2 or keys(n1, elig, dropped) != keys(n2, elig, dropped):
        c = "UNSTABLE"
    else:
        c = "OK"
    classes[p] = c
    extras[p] = (elig, dropped, kn)

frame = {p: c for p, c in classes.items() if p not in CAL}
cal = {p: c for p, c in classes.items() if p in CAL}
elig_frame = [p for p, c in frame.items() if not c.startswith("EXCLUDED")]
brk = sorted(p for p in elig_frame if frame[p].startswith("BREAK"))
print("projects", len(classes), Counter(classes.values()))
print("eligible non-calibration", len(elig_frame), "BREAK", len(brk), Counter(frame[p] for p in brk))
print("BREAK_IMPORT", sorted(p for p in brk if frame[p] == "BREAK_IMPORT"))
print("BREAK_REIFY", sorted(p for p in brk if frame[p] == "BREAK_REIFY"))
print("calibration", sorted(cal.items()))

# Filter arm (deny or eco): fixed = no key present in both filter runs and in neither normal run
fixed, notfixed = [], []
for p in sorted([*brk, *[q for q, c in cal.items() if c.startswith("BREAK")]]):
    elig, dropped, kn = extras[p]
    d1, d2 = load(p, FIX_ARM, 1), load(p, FIX_ARM, 2)
    if d1 is None or d2 is None:
        notfixed.append((p, "no filter runs")); continue
    left = (keys(d1, elig, dropped) & keys(d2, elig, dropped)) - kn
    (fixed if not left else notfixed).append(p if not left else (p, len(left)))
print(FIX_ARM, "fixed", len(fixed), fixed)
print(FIX_ARM, "not fixed", len(notfixed), notfixed)

# Safety: units OK under all that the filter arm turns into a break
worse = []
for p, c in classes.items():
    if c != "OK" or p not in extras:
        continue
    elig, dropped, kn = extras[p]
    d1, d2 = load(p, FIX_ARM, 1), load(p, FIX_ARM, 2)
    if d1 is None or d2 is None:
        continue
    if (keys(d1, elig, dropped) & keys(d2, elig, dropped)) - kn:
        worse.append(p)
print(FIX_ARM, "new breaks among OK under all", len(worse), worse)
