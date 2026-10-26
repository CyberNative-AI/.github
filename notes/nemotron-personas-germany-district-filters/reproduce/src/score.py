"""Scorer: does the dataset's per-Kreis rate track the Zensus 2022 per-Kreis rate?

Per attribute: Spearman rho, OLS slope b of dataset rate on Zensus rate across Kreise
(unweighted), Kreis-bootstrap 95% CI (2000 resamples, seed 16679); within-Land slope b_w after subtracting each
Land's mean Kreis rate on both sides (Länder with >= 2 Kreise); split-half reliability of the dataset rates;
permutation null for rho. P1 (population share) is the instrument positive control.

Usage: python -I score.py --ref out/ref_kreis.csv --ds out/ds_kreis.csv --out out/score.json
       python -I score.py --selftest --ref out/ref_kreis.csv
"""
import argparse
import csv
import json
import random
import sys
from collections import defaultdict

import numpy as np
from scipy.stats import spearmanr

ATTRS = ["MIG", "OWN", "DIV", "WID", "OLD", "SINGLE"]
SLOPE_ATTRS = {"MIG", "OWN", "DIV", "WID", "OLD"}  # SINGLE: household- vs person-level, rho only
SEED = 16679
B = 2000


def ols(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    xm = x - x.mean()
    return float((xm * (y - y.mean())).sum() / (xm * xm).sum())


def boot_ci(x, y, fn, rng):
    n = len(x)
    vals = []
    for _ in range(B):
        idx = rng.integers(0, n, n)
        vals.append(fn(x[idx], y[idx]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def within(x, y, land):
    x = np.asarray(x, float).copy()
    y = np.asarray(y, float).copy()
    land = np.asarray(land)
    keep = np.zeros(len(x), bool)
    for l in set(land):
        s = land == l
        if s.sum() >= 2:
            x[s] -= x[s].mean()
            y[s] -= y[s].mean()
            keep |= s
    return x[keep], y[keep], land[keep]


def verdict(b_ci, rho):
    if b_ci[0] >= 0.6 and rho >= 0.7:
        return "PRESERVED"
    if b_ci[1] < 0.4:
        return "FLATTENED"
    return "PARTIAL"


BANDS = ["a20bis29", "a30bis39", "a40bis49", "a50bis59", "a60bis69", "a70bis79", "a80undaelter"]
AGE_ADJ = ["MIG", "OWN", "DIV", "WID"]  # OLD is age itself; SINGLE is rho-only


def p1_check(ref, ds, ags, rng):
    xp = np.array([ref[a]["pop"] for a in ags]) / sum(ref[a]["pop"] for a in ags)
    yp = np.array([ds[a]["N"] for a in ags]) / sum(ds[a]["N"] for a in ags)
    lr = np.abs(np.log(yp / xp))
    # same-name city/Landkreis pairs that differ >= 15% in Zensus population must keep their order
    by = defaultdict(list)
    for i, a in enumerate(ags):
        by[(ref[a]["SN_L"], ref[a]["GEN"])].append(i)
    flips = []
    for k, ii in by.items():
        if len(ii) == 2:
            i, j = ii
            if max(xp[i], xp[j]) / min(xp[i], xp[j]) >= 1.15 and (xp[i] > xp[j]) != (yp[i] > yp[j]):
                flips.append(k[1])
    r = {"rho": float(spearmanr(xp, yp).statistic), "b": ols(xp, yp), "b_ci": boot_ci(xp, yp, ols, rng),
         "max_abs_log_ratio": float(lr.max()), "worst_kreis": ags[int(lr.argmax())], "pair_flips": flips}
    r["pass"] = (r["rho"] >= 0.95 and 0.8 <= r["b"] <= 1.2 and r["max_abs_log_ratio"] < float(np.log(1.5))
                 and not flips)
    return r


def score(ref: dict, ds: dict, nat_r: dict) -> dict:
    """ref/ds: AGS -> {attr: rate, 'w': age weights (7 bins, 20+)}, ref adds SN_L/GEN/pop, ds adds N and halves 'h'.
    nat_r: attr -> dataset national rate per age band (7), used to age-standardise BOTH sides."""
    rng = np.random.default_rng(SEED)
    ags = sorted(ref)
    land = [ref[a]["SN_L"] for a in ags]
    out = {"n_kreise": len(ags)}
    out["P1"] = p1_check(ref, ds, ags, rng)
    for at in ATTRS:
        x = np.array([ref[a][at] for a in ags])
        y = np.array([ds[a][at] for a in ags])
        r = {"zensus_sd": float(x.std(ddof=1)), "ds_sd": float(y.std(ddof=1)),
             "zensus_range": [float(x.min()), float(x.max())], "ds_range": [float(y.min()), float(y.max())]}
        if not (np.isfinite(x).all() and np.isfinite(y).all()) or r["ds_sd"] == 0 or r["zensus_sd"] == 0:
            r["verdict"] = "INVALID"
            out[at] = r
            continue
        r.update({"rho": float(spearmanr(x, y).statistic), "b": ols(x, y), "b_ci": boot_ci(x, y, ols, rng)})
        h0 = np.array([ds[a]["h"][0][at] for a in ags])
        h1 = np.array([ds[a]["h"][1][at] for a in ags])
        r["split_half_r"] = float(np.corrcoef(h0, h1)[0, 1])
        perm = []
        prng = random.Random(SEED)
        for _ in range(1000):
            yy = list(y)
            prng.shuffle(yy)
            perm.append(spearmanr(x, yy).statistic)
        r["perm_rho_p975"] = float(np.percentile(perm, 97.5))
        xw, yw, _ = within(x, y, land)
        r["b_w"] = ols(xw, yw)
        r["b_w_ci"] = boot_ci(xw, yw, ols, rng)
        r["rho_w"] = float(spearmanr(xw, yw).statistic)
        if at in AGE_ADJ:
            rb = np.asarray(nat_r[at], float)
            ex = np.array([ref[a]["w"] @ rb for a in ags])
            ey = np.array([ds[a]["w"] @ rb for a in ags])
            xa, ya = x - ex, y - ey
            r["b_age"] = ols(xa, ya)
            r["b_age_ci"] = boot_ci(xa, ya, ols, rng)
            r["rho_age"] = float(spearmanr(xa, ya).statistic)
            r["age_expected_sd_zensus"] = float(ex.std(ddof=1))
        if at in SLOPE_ATTRS:
            r["verdict"] = verdict(r["b_ci"], r["rho"])
            r["verdict_within_land"] = verdict(r["b_w_ci"], r["rho_w"])
            if r["verdict"] != "FLATTENED" and r["verdict_within_land"] == "FLATTENED":
                r["verdict"] = "LAND_ONLY"
            if at in AGE_ADJ and r["verdict"] in ("PRESERVED", "PARTIAL") and r["b_age_ci"][1] < 0.4:
                r["verdict"] = "AGE_ONLY"
        else:
            r["verdict"] = "TRACKS" if r["rho"] >= 0.7 else ("UNRELATED" if r["rho"] <= r["perm_rho_p975"] else "WEAK")
        out[at] = r
    flagged = [a for a in SLOPE_ATTRS if out[a]["verdict"] in ("FLATTENED", "LAND_ONLY", "AGE_ONLY")]
    invalid = [a for a in ATTRS if out[a]["verdict"] == "INVALID"]
    out["instrument_valid"] = out["P1"]["pass"] and not invalid
    out["H1"] = {"flagged": sorted(flagged), "invalid": invalid,
                 "supported": bool(flagged) and out["instrument_valid"]}
    return out


def _w(vals):
    v = np.asarray(vals, float)
    return v / v.sum()


def load_ref(path):
    ref = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        d = {"SN_L": r["SN_L"], "GEN": r["GEN"], "pop": float(r["pop_all"]),
             "w": _w([float(r[f"AGEW_{b}"]) for b in BANDS])}
        for at in ATTRS:
            den = float(r[f"{at}_den"])
            d[at] = float(r[f"{at}_num"]) / den if den > 0 else float("nan")
        ref[r["AGS"]] = d
    return ref


def load_ds(path):
    acc = defaultdict(lambda: defaultdict(float))
    halves = defaultdict(lambda: {0: defaultdict(float), 1: defaultdict(float)})
    nat = defaultdict(float)
    for r in csv.DictReader(open(path, encoding="utf-8")):
        h = int(r["half"])
        for k, v in r.items():
            if k in ("AGS", "half"):
                continue
            acc[r["AGS"]][k] += float(v)
            halves[r["AGS"]][h][k] += float(v)
            nat[k] += float(v)
    div = lambda n, d: n / d if d > 0 else float("nan")
    ds = {}
    for a, c in acc.items():
        d = {"N": c["N"], "h": {}, "w": _w([c[f"N_{b}"] for b in BANDS])}
        for at in ATTRS:
            d[at] = div(c[f"{at}_num"], c[f"{at}_den"])
        for h in (0, 1):
            d["h"][h] = {at: div(halves[a][h][f"{at}_num"], halves[a][h][f"{at}_den"]) for at in ATTRS}
        ds[a] = d
    nat_r = {at: [div(nat[f"{at}_num_{b}"], nat[f"{at}_den_{b}"]) for b in BANDS] for at in AGE_ADJ}
    return ds, nat_r


SYN_R = {at: list(np.linspace(lo, hi, 7)) for at, lo, hi in
         (("MIG", 0.25, 0.10), ("OWN", 0.2, 0.6), ("DIV", 0.05, 0.2), ("WID", 0.0, 0.6))}


def synth(ref, mode, rng, n_per=2500):
    """Planted datasets: 'track' (rate = Zensus Kreis rate), 'national' (national mean everywhere), 'land'
    (Land mean of Kreis rates), 'age_only' (rate = Kreis Zensus age weights x a fixed national age gradient),
    'swap' (track, but the München city/Landkreis record counts are swapped: P1 must fail)."""
    ags = sorted(ref)
    nat = {at: float(np.mean([ref[a][at] for a in ags])) for at in ATTRS}
    landmean = defaultdict(dict)
    for at in ATTRS:
        for l in {ref[a]["SN_L"] for a in ags}:
            landmean[l][at] = float(np.mean([ref[a][at] for a in ags if ref[a]["SN_L"] == l]))
    meanpop = np.mean([ref[b]["pop"] for b in ags])
    ds = {}
    for a in ags:
        n = max(400, int(n_per * ref[a]["pop"] / meanpop))
        p = {}
        for at in ATTRS:
            if mode in ("track", "swap"):
                p[at] = ref[a][at]
            elif mode == "national":
                p[at] = nat[at]
            elif mode == "land":
                p[at] = landmean[ref[a]["SN_L"]][at]
            else:
                p[at] = float(ref[a]["w"] @ np.asarray(SYN_R[at])) if at in SYN_R else ref[a][at]
        d = {"N": n, "h": {0: {}, 1: {}}, "w": ref[a]["w"]}
        for at in ATTRS:
            k0 = rng.binomial(n // 2, p[at])
            k1 = rng.binomial(n - n // 2, p[at])
            d[at] = (k0 + k1) / n
            d["h"][0][at] = k0 / (n // 2)
            d["h"][1][at] = k1 / (n - n // 2)
        ds[a] = d
    if mode == "swap":
        city = next(a for a in ags if ref[a]["GEN"] == "München" and a.endswith("162"))
        lk = next(a for a in ags if ref[a]["GEN"] == "München" and a != city)
        ds[city]["N"], ds[lk]["N"] = ds[lk]["N"], ds[city]["N"]
    return ds


def selftest(ref_path):
    ref = load_ref(ref_path)
    rng = np.random.default_rng(1)
    want = {"track": ({"PRESERVED"}, True), "national": ({"FLATTENED"}, True),
            "land": ({"LAND_ONLY", "FLATTENED"}, True), "age_only": ({"AGE_ONLY", "FLATTENED"}, True),
            "swap": ({"PRESERVED"}, False)}
    ok = True
    for mode, (okset, p1) in want.items():
        s = score(ref, synth(ref, mode, rng), SYN_R)
        got = {a: s[a]["verdict"] for a in sorted(SLOPE_ATTRS)}
        check = {a: v for a, v in got.items() if (a in SYN_R or mode != "age_only")}
        bad = {a: v for a, v in check.items() if v not in okset}
        print(mode, "P1", s["P1"]["pass"], s["P1"]["pair_flips"], round(s["P1"]["max_abs_log_ratio"], 3), got,
              "SINGLE", s["SINGLE"]["verdict"])
        if s["P1"]["pass"] != p1 or bad:
            ok = False
    # INVALID guard: an all-zero numerator (label mismatch) must not read as FLATTENED
    d = synth(ref, "track", rng)
    for a in d:
        d[a]["MIG"] = 0.0
    s = score(ref, d, SYN_R)
    print("zero-numerator MIG ->", s["MIG"]["verdict"], "instrument_valid", s["instrument_valid"])
    ok = ok and s["MIG"]["verdict"] == "INVALID" and not s["instrument_valid"]
    print("selftest", "ok" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--ds")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.ref)
    ds, nat_r = load_ds(a.ds)
    s = score(load_ref(a.ref), ds, nat_r)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps({k: (v.get("verdict") if isinstance(v, dict) and "verdict" in v else v) for k, v in s.items()
                      if k not in ("P1",)}, sort_keys=True))
    print("P1", json.dumps(s["P1"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
