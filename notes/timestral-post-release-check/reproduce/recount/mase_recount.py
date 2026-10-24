"""Recompute per-series MASE from raw forecasts + frames (stdlib only), compare with score-all.json per_series."""
import json, sys, datetime as dt
from pathlib import Path
frames = json.load(open(sys.argv[1])); out = Path(sys.argv[2]); score = json.load(open(sys.argv[3]))
def interp(v):
    v = list(v); idx = [i for i, x in enumerate(v) if x is not None]
    for i, x in enumerate(v):
        if x is None:
            lo = max([j for j in idx if j < i], default=None); hi = min([j for j in idx if j > i], default=None)
            v[i] = v[hi] if lo is None else v[lo] if hi is None else v[lo] + (v[hi]-v[lo])*(i-lo)/(hi-lo)
    return v
worst, n = 0.0, 0
for arm in ("FRESH", "PRE"):
    for dom in ("E", "W"):
        W = frames["windows"][dom]
        for f in sorted((out/arm/dom).glob("*.json")):
            m = f.stem; fc = json.loads(f.read_text())["fc"]; acc = {}
            for key, q in fc.items():
                sid, o = key.split("|"); s = frames[dom][sid]
                hourly = s["step"] == "1h"; step = dt.timedelta(hours=1) if hourly else dt.timedelta(days=1)
                t0 = dt.datetime.fromisoformat(s["t0"].replace("Z", "+00:00")); od = dt.datetime.fromisoformat(o.replace("Z", "+00:00"))
                i0 = int(((od + step if hourly else od) - t0) / step)
                ctx = interp(s["values"][i0-W["ctx"]:i0]); y = s["values"][i0:i0+W["h"]]; k = W["m"]
                scale = sum(abs(ctx[i]-ctx[i-k]) for i in range(k, len(ctx))) / (len(ctx)-k)
                med = [row[4] for row in q]
                acc.setdefault(sid, []).append(sum(abs(a-b) for a, b in zip(y, med)) / len(y) / scale)
            ref = score[f"{arm}/{dom}"]["per_series"][m]
            for sid, v in acc.items():
                r = abs(sum(v)/len(v) - ref[sid][0]) / ref[sid][0]; worst = max(worst, r); n += 1
            assert set(acc) == set(ref), (arm, dom, m)
print(f"series-model cells compared: {n}; worst relative difference vs scorer: {worst:.2e}")
