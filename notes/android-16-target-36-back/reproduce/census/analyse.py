"""Census tally. Usage: analyse.py frame.json play.jsonl scan.jsonl broken_patterns(BP,BK) out.json"""
import json, sys, collections, re
frame = {r["pkg"]: r for r in json.load(open(sys.argv[1]))}
play = {json.loads(l)["pkg"]: json.loads(l) for l in open(sys.argv[2])}
scan = {json.loads(l)["pkg"]: json.loads(l) for l in open(sys.argv[3])}
broken = set(sys.argv[4].split(",")) if sys.argv[4] else set()
def ver(v):
    m = re.search(r'(\d+)\.(\d+)', v or ""); return (int(m.group(1)), int(m.group(2))) if m else None
rows = []; c = collections.Counter()
for pk, r in frame.items():
    p = play.get(pk, {}).get("play", "MISSING"); s = scan.get(pk, {})
    row = {"pkg": pk, "source": r["source"], "fdroid_target": r["fdroid_target"], "play": p}
    if not s or s.get("error"):
        row["status"] = "SCAN_ERROR"; rows.append(row); c["SCAN_ERROR"] += 1; c["SCAN_ERROR&" + p] += 1; continue
    ht = s.get("head_target"); row["head_target"] = ht; row["head_target_q"] = s.get("head_target_q")
    pat = {"BP": bool(s["bp"]), "BK": bool(s["bk"])}
    hit = any(pat[k] for k in broken)
    row.update(bp=len(s["bp"]), bk=len(s["bk"]), optf=bool(s["optf"]), optt=bool(s["optt"]), fw=s.get("fw", {}))
    bumped = ht is not None and ht >= 36
    risk_src = (not bumped) and hit and not row["optf"] and not row["optt"]
    row["at_risk_any_store"] = risk_src; row["AT_RISK"] = risk_src and p == "ON_PLAY"
    fw = s.get("fw", {}); fwr = []
    if "cordova-android" in fw and (ver(fw["cordova-android"]) or (99,))[0] <= 14: fwr.append("cordova<=14")
    if "react-native" in fw and (ver(fw["react-native"]) or (0, 99)) < (0, 80): fwr.append("rn<0.80")
    row["fw_risk"] = fwr
    rows.append(row)
    c["scanned"] += 1; c["scanned&" + p] += 1
    c["bumped_head"] += bumped; c["unresolved_head"] += ht is None
    c["BP"] += pat["BP"]; c["BK"] += pat["BK"]; c["BP|BK"] += pat["BP"] or pat["BK"]
    c["optf"] += row["optf"]; c["optt"] += row["optt"]
    c["at_risk_any_store"] += risk_src; c["AT_RISK"] += row["AT_RISK"]
    c["AT_RISK_unresolved_head"] += row["AT_RISK"] and ht is None
    for k in ("cordova-android", "react-native", "@capacitor/android", "flutter"): c["fw:" + k] += k in fw
    for f in fwr: c["fwrisk:" + f] += 1; c["fwrisk:" + f + "&" + p] += 1
c["frame"] = len(frame); c["ON_PLAY"] = sum(1 for v in play.values() if v["play"] == "ON_PLAY"); c["PLAY_UNKNOWN"] = sum(1 for v in play.values() if v["play"] == "PLAY_UNKNOWN")
json.dump({"counts": dict(sorted(c.items())), "rows": rows}, open(sys.argv[5], "w"), indent=1)
for k, v in sorted(c.items()): print(f"{k}\t{v}")
