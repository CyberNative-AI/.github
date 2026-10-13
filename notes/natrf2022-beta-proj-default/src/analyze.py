"""Applies the frozen rule (PROTOCOL.md) to out/ncat_a0.jsonl, out/ncat_repeat.jsonl, out/arms.json."""
import json, math, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
A, F = 6378137.0, 1 / 298.257222101  # GRS80
E2 = F * (2 - F)
def dist_m(lat, lon, lat2, lon2):
    """Local horizontal distance (m) using GRS80 meridian/prime-vertical radii at lat (adequate for < 10 m offsets)."""
    phi = math.radians(lat); s = math.sin(phi)
    M = A * (1 - E2) / (1 - E2 * s * s) ** 1.5; N = A / math.sqrt(1 - E2 * s * s)
    dlon = (lon2 - lon + 540) % 360 - 180
    dn = math.radians(lat2 - lat) * M; de = math.radians(dlon) * N * math.cos(phi)
    return math.hypot(dn, de), dn, de
def q(xs, p):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))] if xs else None
def main():
    frame = {p["id"]: p for p in json.loads((HERE / "data" / "frame.json").read_text())}
    a0 = {r["id"]: r for r in (json.loads(l) for l in (HERE / "out" / "ncat_a0.jsonl").read_text().splitlines() if l.strip())}
    rep = [json.loads(l) for l in (HERE / "out" / "ncat_repeat.jsonl").read_text().splitlines() if l.strip()]
    arms = json.loads((HERE / "out" / "arms.json").read_text())
    st = {s: sum(1 for r in a0.values() if r["status"] == s) for s in ("VALID", "NA", "ERROR")}
    valid = [i for i in frame if a0.get(i, {}).get("status") == "VALID"]
    res = {"counts": st, "n_frame": len(frame), "n_valid": len(valid),
           "n_valid_by_stratum": {s: sum(frame[i]["stratum"] == s for i in valid) for s in ("CONUS", "AK")}}
    # C1 repeat control
    c1 = []
    for r in rep:
        o = a0.get(r["id"], {})
        if r.get("status") == "VALID" and o.get("status") == "VALID":
            c1.append(max(abs(r["out_lat"] - o["out_lat"]), abs(r["out_lon"] - o["out_lon"])))
        else:
            c1.append(None if r.get("status") == o.get("status") else float("inf"))
    res["C1_max_abs_deg"] = c1
    res["C1_n_records"] = len(rep); res["C1_valid_pairs"] = sum(1 for x in c1 if x is not None and x != float("inf"))
    per = {}
    for i in valid:
        o = a0[i]; per[i] = {"stratum": frame[i]["stratum"], "state": frame[i]["state"], "lon": frame[i]["lon"],
                             "ncat_sig_m": (max(o["siglat_m"], o["siglon_m"]) if o.get("siglat_m") is not None and o.get("siglon_m") is not None else None)}
        for arm in ("A1", "A2", "A3"):
            x = arms[arm]["res"].get(i, {})
            per[i][arm] = None if x.get("lat") is None else dist_m(o["out_lat"], o["out_lon"], x["lat"], x["lon"])[0]
    def summ(arm, ids):
        v = [per[i][arm] for i in ids if per[i][arm] is not None]
        return {"n": len(v), "missing": len(ids) - len(v), "median_m": q(v, .5), "p95_m": q(v, .95), "max_m": max(v) if v else None,
                "share_gt_0.05m": (sum(x > 0.05 for x in v) / len(v)) if v else None,
                "share_gt_0.01m": (sum(x > 0.01 for x in v) / len(v)) if v else None,
                "share_gt_0.001m": (sum(x > 0.001 for x in v) / len(v)) if v else None}
    groups = {"ALL": valid, "CONUS": [i for i in valid if frame[i]["stratum"] == "CONUS"], "AK": [i for i in valid if frame[i]["stratum"] == "AK"],
              "CONUS_west_of_-104": [i for i in valid if frame[i]["stratum"] == "CONUS" and frame[i]["lon"] < -104],
              "CONUS_east_of_-104": [i for i in valid if frame[i]["stratum"] == "CONUS" and frame[i]["lon"] >= -104]}
    res["arms"] = {arm: {g: summ(arm, ids) for g, ids in groups.items()} for arm in ("A1", "A2", "A3")}
    sv = [i for i in valid if per[i]["A1"] is not None and per[i]["ncat_sig_m"] is not None]
    res["A1_gt_2sigma_share"] = (sum(per[i]["A1"] > 2 * per[i]["ncat_sig_m"] for i in sv) / len(sv)) if sv else None
    # S3 SPCS2022 parity (descriptive)
    s3 = arms.get("S3", {}); d3 = []
    for i, s in s3.items():
        o = a0[i]
        if s.get("n") is None:
            d3.append((i, None)); continue
        d3.append((i, max(abs(s["n"] - float(o["spc_n"])), abs(s["e"] - float(o["spc_e"])))))
    res["S3"] = {"n": len(d3), "unmapped_or_failed": sum(1 for _, d in d3 if d is None),
                 "max_abs_m": max((d for _, d in d3 if d is not None), default=None),
                 "n_gt_0.0015m": sum(1 for _, d in d3 if d is not None and d > 0.0015),
                 "examples_gt": [(i, d, s3[i]["zone_label"]) for i, d in d3 if d is not None and d > 0.0015][:20]}
    # Frozen rule (v2 after pre-freeze critique)
    reasons = []
    for arm in ("A1", "A2", "A3"):
        if arms[arm]["rc"] != 0 or arms[arm]["n_lines"] != arms[arm]["n_pts"]: reasons.append(f"{arm} container rc/lines mismatch")
    if st["ERROR"] > 0.05 * len(frame): reasons.append("ERROR > 5% of frame")
    if res["C1_n_records"] < 10 or res["C1_valid_pairs"] < 8: reasons.append("C1 incomplete (< 10 records or < 8 VALID pairs)")
    if any(x is not None and x > 1e-10 for x in c1): reasons.append("C1 repeat differs > 1e-10 deg (NCAT changed mid-run)")
    if res["n_valid_by_stratum"]["CONUS"] < 150 or res["n_valid_by_stratum"]["AK"] < 15: reasons.append("INSUFFICIENT valid points")
    # A1 failures ('*' lines) stay in the denominator and count as NOT > 5 cm (conservative toward STOP)
    a1_fail = sum(1 for i in valid if per[i]["A1"] is None)
    s = (sum(1 for i in valid if per[i]["A1"] is not None and per[i]["A1"] > 0.05) / len(valid)) if valid else None
    res["A1_failed_points"] = a1_fail
    # A3 drift is a finding about NCAT vs the 2026-09-18 grids, not a harness failure (harness control = input echo)
    res["A3_drift_finding"] = res["arms"]["A3"]["ALL"]["share_gt_0.01m"]
    if s is None: reasons.append("no VALID points")
    if reasons: verdict = "INVALID"
    elif s >= 0.25: verdict = "CONTINUE"
    elif s < 0.05: verdict = "STOP"
    else: verdict = "CHANGE"
    res["verdict"] = verdict; res["invalid_reasons"] = reasons; res["primary_share_A1_gt_5cm"] = s
    res["per_point"] = per
    (HERE / "out" / "results.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("per_point",)}, indent=1))
if __name__ == "__main__":
    main()
