"""Check the note's two tables and its figures against the raw result files in results/. Exit 1 on any difference."""
import json, re, sys, collections
import xml.etree.ElementTree as ET
from pathlib import Path

here = Path(__file__).resolve().parent
note = (here.parent / "README.md").read_text(encoding="utf-8")
res = here / "results"
bad = []

def kv(s):
    return dict(re.findall(r"(\w+)=(\S+)", s)) if s else None

cells = collections.defaultdict(list)
for dev in ("P36", "T36", "P35", "T35"):
    for line in (res / f"cells-{dev}.jsonl").read_text().splitlines():
        j = json.loads(line)
        if "arm" not in j or j.get("rep") == 0:
            continue
        cells[(dev, j["flavor"], j["arm"])].append((kv(j["start"]), kv(j["after"])))

def one(cs, f):
    labels = {f(s, a) for s, a in cs}
    if len(cs) != 2 or len(labels) != 1:
        return "repeats disagree"
    return labels.pop()

def bar(s, a):
    return "under the status bar" if int(s["top"]) < int(s["inset"]) else "below the status bar"

def lock(s, a):
    if s["ori"] == "P":
        return "portrait, pillarboxed" if s["win"] != s["max"] else "portrait"
    out = "landscape, full screen" if s["win"] == s["max"] else "landscape, windowed"
    if a and int(a["creates"]) > int(s["creates"]):
        out += ", recreated on rotation"
    return out

def table(cols):
    t = {}
    for line in note.splitlines():
        c = [x.strip().strip("*") for x in line.strip().strip("|").split("|")]
        if len(c) == cols + 1 and not set(line) <= set("|-"):
            t[c[0]] = c[1:]
    return t

e = table(3)
for arm, name in (("E1", "Theme sets `windowOptOutEdgeToEdgeEnforcement` to `true`, no inset handling"),
                  ("E0", "No opt-out, no inset handling"), ("E2", "No opt-out, system bar insets applied as padding")):
    got = [one(cells[("P36", "t35", arm)], bar), one(cells[("P36", "t36", arm)], bar), one(cells[("P35", "t36", arm)], bar)]
    if e.get(name) != got:
        bad.append(f"edge-to-edge row {arm}: note {e.get(name)} vs data {got}")

o = table(5)
for arm, name in (("O1", "`screenOrientation=\"portrait\"` in the manifest"), ("O2", "`setRequestedOrientation(PORTRAIT)`"), ("OU", "No lock (control)")):
    got = [one(cells[("T36", fl, arm)], lock) for fl in ("t35", "t36", "t36prop", "t36game")] + [one(cells[("T35", "t36", arm)], lock)]
    if o.get(name) != got:
        bad.append(f"tablet row {arm}: note {o.get(name)} vs data {got}")
for fl in ("t35", "t36"):
    for arm in ("O1", "O2"):
        if one(cells[("P36", fl, arm)], lambda s, a: s["ori"]) != "P":
            bad.append(f"phone lock not held: {fl} {arm}")
s = cells[("T36", "t35", "O1")][0][0]
full = cells[("T36", "t35", "OU")][0][0]
if f"{s['win'].replace('x', ' × ')} portrait window" not in note or f"smallest width {full['sw']} dp" not in note:
    bad.append(f"pillarbox window / smallest width: {s['win']} sw {full['sw']}")
p = cells[("P36", "t35", "E1")][0][0]
if f"the {p['inset']} px status bar" not in note or f"({p['sw']} dp wide)" not in note:
    bad.append(f"phone inset / width: {p['inset']} {p['sw']}")

run1 = collections.defaultdict(list)
for line in (res / "cells-T36-run1.jsonl").read_text().splitlines():
    j = json.loads(line)
    if "arm" in j and j.get("rep", 0) > 0:
        run1[(j["flavor"], j["arm"], j["rep"])] = lock(kv(j["start"]), kv(j["after"]))
rerun = {}
for line in (res / "cells-T36.jsonl").read_text().splitlines():
    j = json.loads(line)
    if "arm" in j and j.get("rep", 0) > 0:
        rerun[(j["flavor"], j["arm"], j["rep"])] = lock(kv(j["start"]), kv(j["after"]))
common = [k for k in run1 if k in rerun and run1[k]]
if any(run1[k] != rerun[k] for k in common) or f"the {len(common)} cells both runs completed agree" not in note:
    bad.append(f"tablet run 1 vs rerun: {len(common)} common cells")

ids = collections.Counter()
for i in ET.parse(res / "lint-t36.xml").getroot().iter("issue"):
    ids[(i.get("id"), i.get("severity"))] += 1
    text = (i.get("message", "") + i.get("errorLine1", "")).lower()
    if "edgetoedge" in text or "edge-to-edge" in text or "themes.xml" in i.find("location").get("file"):
        bad.append(f"lint mentions the opt-out: {i.get('id')}")
if any(sev in ("Error", "Fatal") for _, sev in ids):
    bad.append(f"lint has an error: {dict(ids)}")
for k in ("LockedOrientationActivity", "SourceLockedOrientationActivity", "DiscouragedApi"):
    if (k, "Warning") not in ids or f"`{k}`" not in note:
        bad.append(f"lint warning {k} missing from report or note")

c = json.loads((res / "census-counts.json").read_text())
k, h = c["pattern_counts"], c["after_reading_targets_by_hand"]
figures = {"source of {} of them": k["scanned"], "{} of the 98 set the edge-to-edge opt-out": h["opt_out_not_at_36"],
           "For {} of these we followed": h["opt_out_theme_traced"], "{} of the 98 lock orientation": h["lock_not_at_36_no_property_no_game_category"],
           "For {} of these 20": h["lock_target_chosen_at_build_time"], "{} of the 20 are listed as games": h["lock_listed_as_game_on_fdroid"],
           "{} apps in the 98 already declare it": h["declares_appCategory_game"], "{} apps are in both groups": h["in_both_groups"]}
for phrase, n in figures.items():
    if phrase.format(n) not in note:
        bad.append(f"census figure not in note: '{phrase.format(n)}'")
if h["opt_out_not_at_36"] + h["opt_out_already_at_36"] != k["E"] or h["opt_out_theme_traced"] + h["opt_out_theme_not_traced"] != h["opt_out_not_at_36"]:
    bad.append("census: opt-out counts do not add up to the pattern matches")
if h["lock_not_at_36_no_property_no_game_category"] + h["lock_already_at_36_or_more"] != k["AT_RISK_O"] or k["GAME"] != h["declares_appCategory_game"] or k["OPT_R"] != 0:
    bad.append("census: lock counts do not add up to the pattern matches")

print("\n".join(bad) if bad else "OK: both tables, lint and census figures match the result files")
sys.exit(1 if bad else 0)
