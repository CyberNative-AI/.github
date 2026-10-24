"""Build the frozen series frames (stdlib only).

E: EIA-930 hourly demand (Demand (MW) (Adjusted)) per balancing authority, UTC end-of-hour.
W: en.wikipedia daily user pageviews for the August 2026 top-viewed articles with complete history.
Writes data/frames.json: {domain: {series_id: {"t0": iso, "values": [...], "ba_forecast": [...]?}}, "windows": ...}
"""
import csv, json, sys, time, urllib.request, urllib.parse, datetime as dt, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BULK = ROOT / "raw"  # put the two EIA930_BALANCE_2026 CSVs here (published copy; the run used a host directory)
UA = "cybernative-research/1.0 (hello@cybernative.ai)"
H = dt.timedelta(hours=1)

WINDOWS = {
    "E": {"ctx": 2048, "h": 24, "m": 24,
          "FRESH": [f"2026-10-{d:02d}T00:00:00Z" for d in range(16, 23)],
          "PRE": [f"2026-09-{d:02d}T00:00:00Z" for d in range(16, 23)],
          "PILOT": ["2026-08-10T00:00:00Z"]},
    "W": {"ctx": 512, "h": 7, "m": 7,
          "FRESH": ["2026-10-16T00:00:00Z", "2026-10-17T00:00:00Z"],
          "PRE": ["2026-09-16T00:00:00Z", "2026-09-17T00:00:00Z"],
          "PILOT": ["2026-08-10T00:00:00Z"]},
}

def num(s):
    s = (s or "").replace(",", "").strip()
    return float(s) if s else None

def parse_utc(s):
    return dt.datetime.strptime(s, "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=dt.timezone.utc)

def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")

def build_e():
    files = ["EIA930_BALANCE_2026_Jan_Jun.csv", "EIA930_BALANCE_2026_Jul_Dec.csv"]
    dem, fc = {}, {}
    for f in files:
        with open(BULK / f, newline="") as fh:
            for r in csv.DictReader(fh):
                ba, t = r["Balancing Authority"], parse_utc(r["UTC Time at End of Hour"])
                dem.setdefault(ba, {})[t] = num(r["Demand (MW) (Adjusted)"])
                fc.setdefault(ba, {})[t] = num(r["Demand Forecast (MW)"])
    w = WINDOWS["E"]
    t_start = min(dt.datetime.fromisoformat(o.replace("Z", "+00:00")) for o in w["PILOT"]) - w["ctx"] * H
    t_end = max(dt.datetime.fromisoformat(o.replace("Z", "+00:00")) for o in w["FRESH"]) + w["h"] * H
    out, excl = {}, {}
    for ba in sorted(dem):
        n = int((t_end - t_start) / H)
        times = [t_start + (i + 1) * H for i in range(n)]  # end-of-hour stamps
        vals = [dem[ba].get(t) for t in times]
        why = check(vals, times, w)
        if why:
            excl[ba] = why
            continue
        out[ba] = {"t0": iso(times[0]), "step": "1h", "values": vals,
                   "ba_forecast": [fc[ba].get(t) for t in times]}
    return out, excl

def check(vals, times, w):
    """Inclusion: every target value present and > 0 in every window; context <=5% missing; median >= floor."""
    idx = {t: i for i, t in enumerate(times)}
    step = times[1] - times[0]
    for arm in ("FRESH", "PRE", "PILOT"):
        for o in w[arm]:
            o = dt.datetime.fromisoformat(o.replace("Z", "+00:00"))
            i0 = idx.get(o + step) if step == H else idx.get(o)
            if i0 is None or i0 - w["ctx"] < 0 or i0 + w["h"] > len(vals):
                return f"window {arm} {o} out of range"
            tgt = vals[i0:i0 + w["h"]]
            if any(v is None or v <= 0 for v in tgt):
                return f"target gap/nonpositive {arm} {o}"
            ctx = vals[i0 - w["ctx"]:i0]
            if sum(v is None for v in ctx) > 0.05 * w["ctx"]:
                return f"context >5% missing {arm} {o}"
    present = sorted(v for v in vals if v is not None)
    if present[len(present) // 2] < (100 if step == H else 0):
        return "median below floor"
    return None

def get(url):
    for k in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 ** k)
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2 ** k + 1)
    raise RuntimeError(url)

def build_w(n_target=150):
    top = get("https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2026/08/all-days")
    arts = [a["article"] for a in top["items"][0]["articles"]]
    (BULK / "wiki_top_2026_08.json").write_text(json.dumps(top))
    w = WINDOWS["W"]
    d0, d1 = dt.date(2024, 1, 1), dt.date(2026, 10, 23)
    days = [d0 + dt.timedelta(days=i) for i in range((d1 - d0).days + 1)]
    out, excl = {}, {}
    for a in arts:
        if len(out) >= n_target:
            break
        if ":" in a or a in ("Main_Page", "-") or a.startswith("Special"):
            excl[a] = "namespace/main"
            continue
        url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
               + urllib.parse.quote(a, safe="") + f"/daily/{d0:%Y%m%d}00/{d1:%Y%m%d}00")
        d = get(url)
        time.sleep(0.1)
        if not d:
            excl[a] = "no data"
            continue
        m = {it["timestamp"][:8]: it["views"] for it in d["items"]}
        vals = [m.get(f"{x:%Y%m%d}") for x in days]
        if any(v is None for v in vals):
            excl[a] = "incomplete history"
            continue
        # one value per day; origin at 00:00 of day D -> first target is day D (index of D)
        times = [dt.datetime(x.year, x.month, x.day, tzinfo=dt.timezone.utc) for x in days]
        why = check_daily(vals, times, w)
        if why:
            excl[a] = why
            continue
        out[a] = {"t0": iso(times[0]), "step": "1d", "values": [float(v) for v in vals]}
    return out, excl

def check_daily(vals, times, w):
    idx = {t: i for i, t in enumerate(times)}
    for arm in ("FRESH", "PRE", "PILOT"):
        for o in w[arm]:
            i0 = idx.get(dt.datetime.fromisoformat(o.replace("Z", "+00:00")))
            if i0 is None or i0 - w["ctx"] < 0 or i0 + w["h"] > len(vals):
                return f"window {arm} {o} out of range"
            if any(v <= 0 for v in vals[i0:i0 + w["h"]]):
                return "nonpositive target"
    return None

if __name__ == "__main__":
    e, ee = build_e()
    wv, we = build_w()
    frames = {"windows": WINDOWS, "E": e, "W": wv, "excluded": {"E": ee, "W": we},
              "sources": {f: hashlib.sha256((BULK / f).read_bytes()).hexdigest()
                          for f in ["EIA930_BALANCE_2026_Jan_Jun.csv", "EIA930_BALANCE_2026_Jul_Dec.csv", "wiki_top_2026_08.json"]}}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "frames.json").write_text(json.dumps(frames))
    print("E kept", len(e), "excluded", len(ee)); print("W kept", len(wv), "excluded", len(we))
    print(json.dumps(frames["sources"], indent=1))
