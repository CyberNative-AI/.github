"""Post-run controls (no change to frozen scoring).
C1 alignment: EIA BA day-ahead forecast MAE vs actual at shifts -2..+2 h (correct alignment should minimise at 0).
C2 seasonal-naive identity: statsforecast SeasonalNaive median == last m context values (same input arrays).
C3 raw spot rows for PJM and one Wikipedia article.
C4 leave-top-out: Timestral-209M/Chronos-2 ratio on FRESH without the 5 series with largest |log ratio|."""
import json, sys, datetime as dt
import numpy as np
sys.path.insert(0, "/opt/src")
from score import windows
frames = json.load(open("/opt/data/frames.json"))
out = "/opt/out"
def load(arm, dom, m): return json.load(open(f"{out}/{arm}/{dom}/{m}.json"))["fc"]
res = {}
# C1
s_err = {k: [] for k in range(-2, 3)}
for sid, s in frames["E"].items():
    v = np.array([np.nan if x is None else x for x in s["values"]], float)
    f = np.array([np.nan if x is None else x for x in s["ba_forecast"]], float)
    t0 = dt.datetime.fromisoformat(s["t0"].replace("Z", "+00:00"))
    i0 = round((dt.datetime(2026, 10, 16, 1, tzinfo=dt.timezone.utc) - t0) / dt.timedelta(hours=1))
    for k in s_err:
        a = v[i0 + 2:i0 + 146]; b = f[i0 + 2 + k:i0 + 146 + k]
        ok = ~np.isnan(a) & ~np.isnan(b)
        s_err[k].append(np.mean(np.abs(a[ok] - b[ok]) / np.mean(a[ok])))
res["C1_ba_forecast_rel_mae_by_shift"] = {k: float(np.median(x)) for k, x in s_err.items()}
# C2
from run import tasks
mism = 0; n = 0
for arm in ("FRESH",):
    for dom in ("E", "W"):
        T, h, m = tasks(frames, arm, dom)
        sn = load(arm, dom, "SeasonalNaive")
        for key, ctx in T:
            n += 1
            mism += int(not np.allclose(np.array(sn[key])[:, 4], ctx[-m:][:h]))
res["C2_snaive_identity"] = {"n": n, "mismatch": mism}
# C3
w = windows(frames, "FRESH", "E")
key = "PJM|2026-10-16T00:00:00Z"
sid, y, scale, ba = w[key]
res["C3_PJM_1016"] = {"y": y.tolist(), "T209": [round(r[4]) for r in load("FRESH", "E", "Timestral-209M")[key]],
                      "C2": [round(r[4]) for r in load("FRESH", "E", "Chronos-2")[key]], "BA": ba.tolist()}
ww = windows(frames, "FRESH", "W")
k2 = sorted(ww)[0]
res["C3_W_" + k2] = {"y": ww[k2][1].tolist(), "T209": [round(r[4]) for r in load("FRESH", "W", "Timestral-209M")[k2]],
                     "SN": [round(r[4]) for r in load("FRESH", "W", "SeasonalNaive")[k2]]}
# C4
sc = json.load(open("/opt/score/score-fresh.json"))
for dom in ("E", "W"):
    ps = sc[f"FRESH/{dom}"]["per_series"]
    for b in ("Chronos-2", "TimesFM-2.5"):
        r = {s: np.log(ps["Timestral-209M"][s][0] / ps[b][s][0]) for s in ps[b]}
        keep = sorted(r, key=lambda s: abs(r[s]))[:-5]
        res[f"C4_{dom}_T209/{b}_drop5"] = float(np.exp(np.mean([r[s] for s in keep])))
        res[f"C4_{dom}_T209/{b}_top5"] = {s: round(float(np.exp(r[s])), 3) for s in sorted(r, key=lambda s: -abs(r[s]))[:5]}
print(json.dumps(res, indent=1))
