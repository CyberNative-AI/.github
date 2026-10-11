"""Recount the note's numbers from preambles.csv. Standard library only: python3 -I recount.py preambles.csv"""
import csv, sys
from collections import Counter

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
def has(r, pkg): return pkg in r["packages"].split(";")
def failed(r, col, rule): return rule in r[col].split(";")
print(f"preambles: {len(rows)}; local files skipped: {sum(int(r['local_files_skipped']) for r in rows)} "
      f"in {sum(r['local_files_skipped'] != '0' for r in rows)} preambles")
for e, name in (("lualatex", "LuaLaTeX"), ("pdflatex", "pdfLaTeX")):
    el = [r for r in rows if r[f"{e}_eligible"] == "1"]
    ok = sum(r[f"{e}_result"] == "pass" for r in el)
    ok2 = sum(r[f"{e}_result_2pass"] == "pass" for r in el)
    flips = Counter((r[f"{e}_result_2pass"], r[f"{e}_result"]) for r in el if r[f"{e}_result_2pass"] != r[f"{e}_result"])
    print(f"{name}: {ok} of {len(el)} eligible pass when compiled until no rerun request; "
          f"{ok2} of {len(el)} after exactly 2 passes; changed: {dict(flips) or 'none'}")
    print(f"  passes needed: {dict(sorted(Counter(r[f'{e}_passes'] for r in rows).items()))}")
    for flag in ("red", "amber", "green"):
        s = [r for r in el if r["status_report"] == flag]
        print(f"  status report {flag}: {sum(r[f'{e}_result'] == 'pass' for r in s)} of {len(s)} pass")
    print(f"  failures: {dict(Counter(r[f'{e}_result'] for r in el if r[f'{e}_result'] != 'pass'))}")
    for r in el:
        if r[f"{e}_result"] == "fail":
            print(f"    {r['arxiv_id']} {r['class']}: {r[f'{e}_failed_rules']}")
built = [r for r in rows if r["pdflatex_eligible"] == "1" and r["pdflatex_result"] != "compile_error"]
for h in (True, False):
    s = [r for r in built if has(r, "hyperref") == h]
    print(f"pdfLaTeX, compiled, hyperref {'loaded' if h else 'not loaded'} ({len(s)}): rule 8.2.2-1 fails in "
          f"{sum(failed(r, 'pdflatex_failed_rules_2pass', '8.2.2-1') for r in s)} after 2 passes, "
          f"{sum(failed(r, 'pdflatex_failed_rules', '8.2.2-1') for r in s)} when compiled until no rerun request")
