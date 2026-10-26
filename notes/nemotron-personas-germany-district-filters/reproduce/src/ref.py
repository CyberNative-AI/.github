"""Reference side: Zensus 2022 1 km grid cells -> 400 Kreise (VG250_KRS 2022, GF=4) by cell centroid.

Writes out/ref_kreis.csv: per Kreis, numerator/denominator sums per attribute and coverage
(population of cells usable for that attribute / all population in the Kreis, from Bevoelkerungszahl).
A cell is usable for an attribute only when every field the attribute needs is numeric ('–' = suppressed).
Small registered-partnership categories are the exception: '–' counts as 0 there.

Usage (container): python -I ref.py --grid /ref/grid1km --vg /ref/vg/EPSG_25832/VG250_KRS.shp --out /out/ref_kreis.csv
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

FILES = {
    "pop": "Zensus2022_Bevoelkerungszahl_1km-Gitter.csv",
    "geb": "Zensus2022_Geburtsland_Gruppen_1km-Gitter.csv",
    "own": "Zensus2022_Eigentuemerquote_1km-Gitter.csv",
    "fam": "Zensus2022_Familienstand_1km-Gitter.csv",
    "hh": "Zensus2022_Typ_priv_HH_Lebensform_1km-Gitter.csv",
    "age": "Zensus2022_Alter_in_10er-Jahresgruppen_1km-Gitter.csv",
}


def num(s: pd.Series) -> pd.Series:
    """'–' / '' -> NaN; decimal comma -> float."""
    s = s.astype(str).str.strip().str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s.where(~s.isin(["–", "-", "", "nan"])), errors="coerce")


def load(grid: Path, key: str) -> pd.DataFrame:
    df = pd.read_csv(grid / FILES[key], sep=";", dtype=str, encoding="utf-8")
    df = df.rename(columns={"GITTER_ID_1km": "cell"})
    for c in df.columns:
        if c not in ("cell", "werterlaeuternde_Zeichen"):
            df[c] = num(df[c])
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", required=True)
    ap.add_argument("--vg", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    grid = Path(a.grid)

    kr = gpd.read_file(a.vg)
    kr = kr[kr.GF == 4][["AGS", "GEN", "BEZ", "SN_L", "geometry"]].to_crs(3035)
    assert len(kr) == 400, len(kr)

    pop = load(grid, "pop")
    pts = gpd.GeoDataFrame(pop[["cell"]], geometry=gpd.points_from_xy(pop.x_mp_1km, pop.y_mp_1km), crs=3035)
    j = gpd.sjoin(pts, kr[["AGS", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    pop["AGS"] = j["AGS"].values
    miss = pop[pop.AGS.isna()]
    # Centroids outside every Kreis polygon (coast, border): assign to nearest Kreis, report count + population.
    if len(miss):
        near = gpd.sjoin_nearest(pts.loc[miss.index], kr[["AGS", "geometry"]], how="left")
        near = near[~near.index.duplicated()]
        pop.loc[miss.index, "AGS"] = near["AGS"].values
    cell2ags = pop.set_index("cell")["AGS"]
    rows = {ags: {"AGS": ags} for ags in kr.AGS}
    totpop = pop.groupby("AGS")["Einwohner"].sum()
    for ags in rows:
        rows[ags]["pop_all"] = float(totpop.get(ags, 0.0))

    def add(attr: str, df: pd.DataFrame, numer: pd.Series, denom: pd.Series, usable: pd.Series, popcol: pd.Series):
        d = pd.DataFrame({"AGS": df.cell.map(cell2ags), "n": numer, "d": denom, "u": usable, "p": popcol})
        if d.AGS.isna().any():
            print(f"{attr}: {int(d.AGS.isna().sum())} cells not in population grid", file=sys.stderr)
        d = d.dropna(subset=["AGS"])
        g = d[d.u].groupby("AGS")[["n", "d", "p"]].sum()
        for ags in rows:
            r = g.loc[ags] if ags in g.index else None
            rows[ags][f"{attr}_num"] = float(r.n) if r is not None else 0.0
            rows[ags][f"{attr}_den"] = float(r.d) if r is not None else 0.0
            rows[ags][f"{attr}_covpop"] = float(r.p) if r is not None else 0.0

    popmap = pop.set_index("cell")["Einwohner"]

    geb = load(grid, "geb")
    u = geb.Insgesamt_Bevoelkerung.notna() & geb.Deutschland.notna()
    add("MIG", geb, geb.Insgesamt_Bevoelkerung - geb.Deutschland, geb.Insgesamt_Bevoelkerung, u, geb.cell.map(popmap))

    own = load(grid, "own")
    p = own.cell.map(popmap)
    u = own.Eigentuemerquote.notna() & p.notna()
    add("OWN", own, own.Eigentuemerquote / 100.0 * p, p, u, p)

    fam = load(grid, "fam")
    lp = fam[["EingetrLebenspartnerschaft", "EingetrLebenspartVerstorben", "EingetrLebenspartAufgehoben"]].fillna(0)
    ever = fam.Verheiratet + fam.Verwitwet + fam.Geschieden + lp.sum(axis=1)
    u = fam.Verheiratet.notna() & fam.Verwitwet.notna() & fam.Geschieden.notna()
    add("DIV", fam, fam.Geschieden + lp.EingetrLebenspartAufgehoben, ever, u, fam.cell.map(popmap))
    add("WID", fam, fam.Verwitwet + lp.EingetrLebenspartVerstorben, ever, u, fam.cell.map(popmap))

    hh = load(grid, "hh")
    u = hh.Insgesamt_Haushalte.notna() & hh.EinpersHH_SingleHH.notna()
    add("SINGLE", hh, hh.EinpersHH_SingleHH, hh.Insgesamt_Haushalte, u, hh.cell.map(popmap))

    age = load(grid, "age")
    bins = ["a20bis29", "a30bis39", "a40bis49", "a50bis59", "a60bis69", "a70bis79", "a80undaelter"]
    u = age[bins].notna().all(axis=1)
    add("OLD", age, age[["a60bis69", "a70bis79", "a80undaelter"]].sum(axis=1), age[bins].sum(axis=1), u, age.cell.map(popmap))
    # Age weights (20+, 10-year bins, usable OLD cells) for the age-standardised readout
    ab = age[u].assign(AGS=age[u].cell.map(cell2ags)).dropna(subset=["AGS"]).groupby("AGS")[bins].sum()
    for ags in rows:
        for b in bins:
            rows[ags][f"AGEW_{b}"] = float(ab.loc[ags, b]) if ags in ab.index else 0.0

    meta = kr.drop(columns="geometry").set_index("AGS")
    out = []
    for ags, r in rows.items():
        r.update({"GEN": meta.loc[ags, "GEN"], "BEZ": meta.loc[ags, "BEZ"], "SN_L": meta.loc[ags, "SN_L"]})
        out.append(r)
    out.sort(key=lambda r: r["AGS"])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    summ = {"cells": int(len(pop)), "cells_nearest_assigned": int(len(miss)),
            "pop_nearest_assigned": float(miss.Einwohner.sum()), "pop_total": float(pop.Einwohner.sum())}
    print(json.dumps(summ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
