"""Runner. Usage: run.py ARM DOMAIN MODEL OUTDIR   (inside the container, network none).
Every model gets identical contexts: the last `ctx` values before the origin, missing values linearly interpolated.
Writes OUTDIR/ARM/DOMAIN/MODEL.json = {"meta": {...}, "fc": {"<sid>|<origin>": {"q": [[q.1..q.9] x h]}}}"""
import json, sys, time, datetime as dt, os
from pathlib import Path
import numpy as np

QL = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
HF = json.load(open("/opt/hf/paths.json"))

def tasks(frames, arm, dom):
    w = frames["windows"][dom]
    out = []
    for sid, s in frames[dom].items():
        t0 = dt.datetime.fromisoformat(s["t0"].replace("Z", "+00:00"))
        step = dt.timedelta(hours=1) if s["step"] == "1h" else dt.timedelta(days=1)
        for o in w[arm]:
            od = dt.datetime.fromisoformat(o.replace("Z", "+00:00"))
            # E stamps are end-of-hour: first target stamp = origin + 1h. W stamps are day starts: first target = origin.
            first = od + step if s["step"] == "1h" else od
            i0 = round((first - t0) / step)
            ctx = np.array([np.nan if v is None else v for v in s["values"][i0 - w["ctx"]:i0]], dtype=float)
            ok = ~np.isnan(ctx)
            ctx = np.interp(np.arange(len(ctx)), np.flatnonzero(ok), ctx[ok])
            out.append((f"{sid}|{o}", ctx))
    return out, w["h"], w["m"]

def run_timestral(name, T, h):
    import torch
    from timestral import TimestralForecaster
    torch.set_num_threads(int(os.environ.get("NT", "8")))
    m = TimestralForecaster.from_pretrained(HF[f"mistralai/{name}"])
    lv = m.quantile_levels
    idx = [min(range(len(lv)), key=lambda i: abs(lv[i] - q)) for q in QL]
    assert all(abs(lv[i] - q) < 1e-9 for i, q in zip(idx, QL)), lv
    res = {}
    for k in range(0, len(T), 64):
        chunk = T[k:k + 64]
        f = m.forecast(np.stack([c for _, c in chunk]), prediction_length=h)
        q = f.quantiles[:, 0, :, :][..., idx].cpu().numpy()
        for (key, _), qq in zip(chunk, q):
            res[key] = qq.tolist()
    return res

def run_chronos(repo, T, h):
    import torch
    from chronos import BaseChronosPipeline
    torch.set_num_threads(int(os.environ.get("NT", "8")))
    p = BaseChronosPipeline.from_pretrained(HF[repo], device_map="cpu")
    res = {}
    for k in range(0, len(T), 64):
        chunk = T[k:k + 64]
        qs, _ = p.predict_quantiles([torch.tensor(c, dtype=torch.float32) for _, c in chunk],
                                    prediction_length=h, quantile_levels=QL)
        for (key, _), qq in zip(chunk, qs):
            res[key] = qq[0].cpu().numpy().tolist()
    return res

def run_timesfm(T, h, ctx):
    import torch, timesfm
    torch.set_num_threads(int(os.environ.get("NT", "8")))
    m = timesfm.TimesFM_2p5_200M_torch.from_pretrained(HF["google/timesfm-2.5-200m-pytorch"], torch_compile=False)
    # Config as recommended on the model card, with max_context set to the frame context.
    m.compile(timesfm.ForecastConfig(max_context=ctx, max_horizon=256, normalize_inputs=True,
                                     use_continuous_quantile_head=True, force_flip_invariance=True,
                                     infer_is_positive=True, fix_quantile_crossing=True, per_core_batch_size=32))
    res = {}
    for k in range(0, len(T), 64):
        chunk = T[k:k + 64]
        _, q = m.forecast(horizon=h, inputs=[c for _, c in chunk])
        for (key, _), qq in zip(chunk, q[:len(chunk)]):
            res[key] = qq[:, 1:10].tolist()   # index 0 = mean, 1..9 = q0.1..q0.9
    return res

def run_stats(which, T, h, m):
    import pandas as pd
    from statsforecast import StatsForecast
    from statsforecast.models import AutoETS, AutoARIMA, SeasonalNaive, MSTL
    mod = {"AutoETS": AutoETS(season_length=m), "AutoARIMA": AutoARIMA(season_length=m),
           "SeasonalNaive": SeasonalNaive(season_length=m),
           "MSTL": MSTL(season_length=[m, 7 * m] if m == 24 else [m, 365])}[which]
    rows = []
    for key, c in T:
        rows.append(pd.DataFrame({"unique_id": key, "ds": np.arange(len(c)), "y": c}))
    df = pd.concat(rows)
    sf = StatsForecast(models=[mod], freq=1, n_jobs=int(os.environ.get("NT", "8")))
    fc = sf.forecast(df=df, h=h, level=[20, 40, 60, 80])
    res = {}
    for key, g in fc.groupby("unique_id", sort=False):
        g = g.sort_values("ds")
        cols = [f"{which}-lo-80", f"{which}-lo-60", f"{which}-lo-40", f"{which}-lo-20", which,
                f"{which}-hi-20", f"{which}-hi-40", f"{which}-hi-60", f"{which}-hi-80"]
        res[key] = g[cols].to_numpy().tolist()
    return res

if __name__ == "__main__":
    arm, dom, model, outdir = sys.argv[1:5]
    frames = json.load(open("/opt/data/frames.json"))
    T, h, m = tasks(frames, arm, dom)
    t = time.time()
    if model.startswith("Timestral"):
        res = run_timestral(model, T, h)
    elif model == "Chronos-2":
        res = run_chronos("amazon/chronos-2", T, h)
    elif model == "Chronos-2-small":
        res = run_chronos("autogluon/chronos-2-small", T, h)
    elif model == "TimesFM-2.5":
        res = run_timesfm(T, h, frames["windows"][dom]["ctx"])
    else:
        res = run_stats(model, T, h, m)
    wall = time.time() - t
    bad = sum(1 for v in res.values() if not np.all(np.isfinite(np.array(v))))
    p = Path(outdir) / arm / dom
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{model}.json").write_text(json.dumps({"meta": {"arm": arm, "dom": dom, "model": model, "n": len(res),
        "n_tasks": len(T), "nonfinite": bad, "wall_s": round(wall, 2), "threads": os.environ.get("NT", "8")}, "fc": res}))
    print(arm, dom, model, "n", len(res), "nonfinite", bad, "wall", round(wall, 1), flush=True)
