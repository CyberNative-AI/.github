"""Check the note's table and figures against the raw result files in results/. Exit 1 on any difference."""
import json, re, sys, collections
import xml.etree.ElementTree as ET
from pathlib import Path

here = Path(__file__).resolve().parent
note = (here.parent / "README.md").read_text(encoding="utf-8")
res = here / "results"
bad = []

def trials(api):
    t = collections.defaultdict(list)
    for line in (res / f"matrix-API{api}.jsonl").read_text().splitlines():
        r = json.loads(line)
        t[(r["flavor"], r["arm"])].append((r["marker"], r["still_top"]))
    return t

def label(cells, arm):
    if len(set(cells)) != 1:
        return "repeats disagree"
    m, top = cells[0]
    if arm == "NO":
        return "closes" if (m, top) == (0, 0) else f"unexpected {m},{top}"
    if m >= 1 and top == 1:
        return "handled"
    if m == 0 and top == 0:
        return "not called, screen closes"
    if m >= 1 and top == 0:
        return "handler runs, screen closes anyway"
    return f"unexpected {m},{top}"

t36, t35 = trials(36), trials(35)
rows = {"NA": "`Activity.onBackPressed()` override", "XA": "`AppCompatActivity.onBackPressed()` override",
        "NK": "`Activity.onKeyDown()` returns `true` for `KEYCODE_BACK`", "XK": "`AppCompatActivity.onKeyDown()` for `KEYCODE_BACK`",
        "ND": "`android.app.Dialog.onBackPressed()` override", "XD": "AndroidX `OnBackPressedCallback`", "NO": "No handler"}
table = {}
for line in note.splitlines():
    cols = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
    if len(cols) == 5:
        table[cols[0]] = cols[1:]
for arm, name in rows.items():
    on35 = {label(t35[(f, arm)], arm) for f in ("t35", "t36", "t36opt")}
    got = [label(t36[("t35", arm)], arm), label(t36[("t36", arm)], arm), label(t36[("t36opt", arm)], arm),
           on35.pop() if len(on35) == 1 else "differs by build"]
    if table.get(name) != got:
        bad.append(f"table row {arm}: note {table.get(name)} vs data {got}")
for api, t in ((36, t36), (35, t35)):
    if any(len(v) != 2 for (f, a), v in t.items() if a != "CDV"):
        bad.append(f"API {api}: not 2 repeats per cell")

cdv = {(a, f): v for a, t in ((36, t36), (35, t35)) for (f, arm), v in t.items() if arm == "CDV"}
expect = {(36, "f14t36"): (1, 0), (36, "f15t36"): (2, 1), (35, "f15t36"): (1, 1), (36, "f14t35"): (1, 1), (35, "f14t36"): (1, 1)}
for k, v in expect.items():
    if set(cdv.get(k, [])) != {v}:
        bad.append(f"cordova {k}: {cdv.get(k)} expected {v}")
blocks = re.split(r"^== ", (res / "cdv-double-API36.txt").read_text(), flags=re.M)[1:]
per = collections.Counter()
for b in blocks:
    head, *lines = b.strip().splitlines()
    per[(head.split()[1], sum("BACKPROBE HANDLED CDV" in l for l in lines))] += 1
if per != collections.Counter({("f15t36", 2): 3, ("f14t35", 1): 3}):
    bad.append(f"cordova double-fire log: {dict(per)}")

def lint(f):
    out = collections.defaultdict(set)
    for i in ET.parse(res / f).getroot().iter("issue"):
        out[(i.get("id"), i.get("severity"))].add(Path(i.find("location").get("file")).stem)
    return out
l36, l35 = lint("lintdef-t36.xml"), lint("lintdef-t35.xml")
if l36.get(("GestureBackNavigation", "Error")) != {"NA", "XA", "NK", "XK", "ND"}:
    bad.append(f"lint t36: {dict(l36)}")
if any(k[0] == "GestureBackNavigation" for k in l35):
    bad.append("lint t35 reports GestureBackNavigation")

c = json.loads((res / "census-counts.json").read_text())
k = c["counts_onBackPressed_only"]
hand = c["read_by_hand"]
figures = {"{} apps with source": k["frame"], "{} of them have a Google Play listing": k["ON_PLAY"],
           "source of {} of these": k["scanned&ON_PLAY"], "{} already target 36": c["on_play_scanned_target_36_or_more"],
           "{} of the 99 have an Activity": hand["activity_onBackPressed_override"],
           "For {} of these 23": c["activity_onBackPressed_override_target_unreadable"],
           "{} more intercept only": hand["activity_KEYCODE_BACK_only"]}
for phrase, n in figures.items():
    if phrase.format(n) not in note:
        bad.append(f"census figure not in note: '{phrase.format(n)}'")
if sum(hand.values()) != c["AT_RISK_onBackPressed_or_KEYCODE_BACK"]:
    bad.append("census: hand-read labels do not add up to the pattern matches")

print("\n".join(bad) if bad else "OK: table, Cordova, lint and census figures match the result files")
sys.exit(1 if bad else 0)
