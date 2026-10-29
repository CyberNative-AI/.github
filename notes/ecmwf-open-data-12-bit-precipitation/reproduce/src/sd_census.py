"""Snow depth check (sd/PRE-SD.md). usage: python -I sd_census.py RAWDIR OUT.json"""
import json, sys, pathlib
import numpy as np
import eccodes as ec
raw, outp = pathlib.Path(sys.argv[1]), sys.argv[2]
def load(p):
    d = {}
    with open(p, "rb") as f:
        while (h := ec.codes_grib_new_from_file(f)) is not None:
            sn = ec.codes_get(h, "shortName"); d[sn] = (ec.codes_get_values(h).astype(np.float64), ec.codes_get(h, "bitsPerValue"),
                ec.codes_get(h, "binaryScaleFactor"), ec.codes_get(h, "decimalScaleFactor"), ec.codes_clone(h))
            if sn == "sd": lat = ec.codes_get_array(h, "latitudes"); d["_lat"] = lat
            ec.codes_release(h)
    return d
post = load(raw / "20261028" / "24.grib2")
v28, nb28, E28, D28, _ = post["sd"]; q = (2.0 ** E28) * 10.0 ** (-D28)
res = {"q": q, "post_bits": nb28,
       "C1_multiple_of_q": bool(np.all(np.abs(v28 / q - np.round(v28 / q)) < 1e-6)) and nb28 == 9,
       "post_nonzero_lt_q": int(np.sum((v28 > 0) & (v28 < q))), "dates": {}}
for date in ("20261015", "20261019"):
    d = load(raw / date / "24.grib2")
    sd, nb, _, _, h = d["sd"]; rsn = d["rsn"][0]; land = d["lsm"][0] > 0.5; w = np.cos(np.deg2rad(d["_lat"]))
    R = sd.min(); snow = land & (sd >= 0.001)
    arms = {"NEAREST": R + np.round((sd - R) / q) * q, "FLOOR": R + np.floor((sd - R) / q) * q}
    c = ec.codes_clone(h); ec.codes_set_long(c, "bitsPerValue", 9); ec.codes_set_values(c, sd)
    arms["ECCODES9"] = ec.codes_get_values(c).astype(np.float64)
    r = {"pre_bits": nb, "R": R, "n_land": int(land.sum()), "n_snow": int(snow.sum()),
         "snow_area_share_of_land": float(w[snow].sum() / w[land].sum()),
         "eccodes9_bits": ec.codes_get(c, "bitsPerValue"), "eccodes9_q": (2.0 ** ec.codes_get(c, "binaryScaleFactor")) * 10.0 ** (-ec.codes_get(c, "decimalScaleFactor")),
         "C2_max_over_q": float(arms["NEAREST"].max() / q), "arms": {}}
    ec.codes_release(c)
    dep16 = sd / np.maximum(rsn, 1.0) * 100.0
    for k, s in arms.items():
        z = snow & (s <= 0)
        dep = s / np.maximum(rsn, 1.0) * 100.0; dd = np.abs(dep - dep16)
        r["arms"][k] = {"Z_count": float(z.sum() / snow.sum()), "Z_area": float(w[z].sum() / w[snow].sum()),
                        "share_depth_change_ge5cm": float((dd[snow] >= 5).mean()),
                        "median_abs_depth_change_cm": float(np.median(dd[snow])),
                        "p90_abs_depth_change_cm": float(np.percentile(dd[snow], 90)),
                        "share_sd_change_ge_10mm": float((np.abs(s - sd)[snow] >= 0.010).mean())}
    # context: distribution of pre-change snow amounts
    r["snow_sd_quantiles_mm"] = {str(p): float(np.percentile(sd[snow] * 1000, p)) for p in (10, 25, 50, 75, 90)}
    r["snow_depth_quantiles_cm"] = {str(p): float(np.percentile(dep16[snow], p)) for p in (10, 25, 50, 75, 90)}
    res["dates"][date] = r
zs = [res["dates"][dt]["arms"]["NEAREST"]["Z_count"] for dt in res["dates"]]
c2 = all(res["dates"][dt]["C2_max_over_q"] < 512 for dt in res["dates"])
c3 = {dt: abs(res["dates"][dt]["arms"]["ECCODES9"]["Z_count"] - res["dates"][dt]["arms"]["NEAREST"]["Z_count"]) <= 0.005 for dt in res["dates"]}
res.update(C2=c2, C3=c3, verdict="INVALID" if not (res["C1_multiple_of_q"] and c2) else
           "CONTINUE" if min(zs) >= 0.10 else "STOP" if max(zs) < 0.02 else "NARROW")
json.dump(res, open(outp, "w"), indent=1, default=float); print(res["verdict"], zs)
