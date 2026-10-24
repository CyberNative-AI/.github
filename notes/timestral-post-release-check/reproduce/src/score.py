"""Scorer. Usage: score.py OUTDIR ARM [ARM...] > results JSON. Stdlib + numpy (host venv not needed: run in container)."""
import json, sys, datetime as dt
from pathlib import Path
import numpy as np

MODELS = ["SeasonalNaive", "AutoETS", "MSTL", "AutoARIMA", "Timestral-5M", "Timestral-28M", "Timestral-209M",
          "Chronos-2-small", "Chronos-2", "TimesFM-2.5"]
QL = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
PAIRS = [("Timestral-209M", "Chronos-2"), ("Timestral-209M", "TimesFM-2.5"), ("Timestral-209M", "AutoETS"), ("Timestral-209M", "MSTL"),
         ("Timestral-209M", "SeasonalNaive"), ("Timestral-209M", "AutoARIMA"), ("Timestral-5M", "Timestral-209M"),
         ("Timestral-28M", "Chronos-2-small"), ("Timestral-209M", "EIA-BA-forecast")]
B = 2000

def windows(frames, arm, dom):
    w = frames["windows"][dom]
    out = {}
    for sid, s in frames[dom].items():
        t0 = dt.datetime.fromisoformat(s["t0"].replace("Z", "+00:00"))
        step = dt.timedelta(hours=1) if s["step"] == "1h" else dt.timedelta(days=1)
        for o in w[arm]:
            od = dt.datetime.fromisoformat(o.replace("Z", "+00:00"))
            first = od + step if s["step"] == "1h" else od
            i0 = round((first - t0) / step)
            ctx = np.array([np.nan if v is None else v for v in s["values"][i0 - w["ctx"]:i0]], dtype=float)
            ok = ~np.isnan(ctx)
            ctx = np.interp(np.arange(len(ctx)), np.flatnonzero(ok), ctx[ok])
            y = np.array(s["values"][i0:i0 + w["h"]], dtype=float)
            m = w["m"]
            scale = np.mean(np.abs(ctx[m:] - ctx[:-m]))
            ba = None
            if "ba_forecast" in s:
                f = s["ba_forecast"][i0:i0 + w["h"]]
                ba = None if any(v is None for v in f) else np.array(f, dtype=float)
            out[f"{sid}|{o}"] = (sid, y, scale, ba)
    return out

def per_series(fc, win):
    """series -> (mean MASE over origins, mean WQL over origins or None)"""
    acc = {}
    for key, (sid, y, scale, ba) in win.items():
        if fc is None:            # EIA BA forecast reference (point only)
            if ba is None:
                return None
            med, q = ba, None
        else:
            q = np.array(fc[key]); med = q[:, 4]
        mase = np.mean(np.abs(y - med)) / scale
        wql = None
        if q is not None:
            e = y[:, None] - q
            wql = float(np.mean(np.sum(2 * np.maximum(QL * e, (QL - 1) * e), axis=0) / np.sum(np.abs(y))))
        acc.setdefault(sid, []).append((mase, wql))
    return {s: (float(np.mean([a for a, _ in v])), None if v[0][1] is None else float(np.mean([b for _, b in v])))
            for s, v in acc.items()}

def gmean_ratio_ci(a, b, sids, rng):
    r = np.log(np.array([a[s][0] for s in sids]) / np.array([b[s][0] for s in sids]))
    boot = [np.mean(r[rng.integers(0, len(r), len(r))]) for _ in range(B)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"ratio": float(np.exp(r.mean())), "lo": float(np.exp(lo)), "hi": float(np.exp(hi)),
            "win_share": float(np.mean(r < 0)), "n": len(r),
            "verdict": "A_BETTER" if np.exp(hi) < 1 else ("B_BETTER" if np.exp(lo) > 1 else "TIE")}

def main(outdir, arms):
    frames = json.load(open("/opt/data/frames.json"))
    res = {}
    for arm in arms:
        for dom in ("E", "W"):
            win = windows(frames, arm, dom)
            ps = {}
            for m in MODELS:
                p = Path(outdir) / arm / dom / f"{m}.json"
                if not p.exists():
                    continue
                d = json.loads(p.read_text())
                assert d["meta"]["nonfinite"] == 0 and d["meta"]["n"] == len(win), (m, d["meta"])
                ps[m] = per_series(d["fc"], win)
                ps[m + "@wall_s"] = d["meta"]["wall_s"]
            if dom == "E":
                ba = per_series(None, {k: v for k, v in win.items()})
                if ba is not None:
                    ps["EIA-BA-forecast"] = ba
            models = [m for m in ps if "@" not in m]
            sids = sorted(ps["SeasonalNaive"])
            sn = ps["SeasonalNaive"]
            table = {}
            for m in models:
                rel = np.array([ps[m][s][0] / sn[s][0] for s in sids])
                wq = [ps[m][s][1] for s in sids]
                table[m] = {"gmean_rel_mase": float(np.exp(np.mean(np.log(rel)))),
                            "mean_mase": float(np.mean([ps[m][s][0] for s in sids])),
                            "mean_wql": None if wq[0] is None else float(np.mean(wq)),
                            "wall_s": ps.get(m + "@wall_s")}
            rng = np.random.default_rng(16235)
            pairs = {f"{a}/{b}": gmean_ratio_ci(ps[a], ps[b], sids, rng) for a, b in PAIRS if a in ps and b in ps}
            res[f"{arm}/{dom}"] = {"n_series": len(sids), "n_tasks": len(win), "table": table, "pairs": pairs,
                                   "per_series": {m: {s: ps[m][s] for s in sids} for m in models}}
    # exploratory leak probe: difference-in-differences of log ratio T209/Chronos-2 (PRE minus FRESH), same series
    for dom in ("E", "W"):
        if f"PRE/{dom}" in res and f"FRESH/{dom}" in res:
            out = {}
            for b in ("Chronos-2", "TimesFM-2.5", "AutoETS"):
                pre, fr = res[f"PRE/{dom}"]["per_series"], res[f"FRESH/{dom}"]["per_series"]
                if b not in pre or b not in fr:
                    continue
                sids = sorted(pre["Timestral-209M"])
                d = np.array([np.log(pre["Timestral-209M"][s][0] / pre[b][s][0]) - np.log(fr["Timestral-209M"][s][0] / fr[b][s][0]) for s in sids])
                rng = np.random.default_rng(16235)
                boot = [np.mean(d[rng.integers(0, len(d), len(d))]) for _ in range(B)]
                lo, hi = np.percentile(boot, [2.5, 97.5])
                out[b] = {"did_ratio": float(np.exp(d.mean())), "lo": float(np.exp(lo)), "hi": float(np.exp(hi)),
                          "flag": bool(np.exp(d.mean()) < 1 / 1.10 and np.exp(hi) < 1)}
            res[f"LEAKPROBE/{dom}"] = out
    print(json.dumps(res))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
