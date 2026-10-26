"""Dataset side: Nemotron-Personas-Germany (rev 1285ad18, 10 shards) -> per-Kreis counts.

Reads only structured columns (no persona text). Maps the dataset's Kreis name + Bundesland to the
VG250 AGS with a deterministic rule (match() below); refuses to continue unless all 400 names map 1:1.
Writes out/ds_kreis.csv with, per AGS and per half (h=0/1 by uuid last hex digit parity, for split-half
reliability), the numerator and denominator of each attribute.

Usage (container): python -I frame.py --data /data --vg /ref/vg/EPSG_25832/VG250_KRS.shp --out /out/ds_kreis.csv
"""
import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import pyarrow.parquet as pq

LAND = {"Schleswig-Holstein": "01", "Hamburg": "02", "Niedersachsen": "03", "Bremen": "04",
        "Nordrhein-Westfalen": "05", "Hessen": "06", "Rheinland-Pfalz": "07", "Baden-Württemberg": "08",
        "Bayern": "09", "Saarland": "10", "Berlin": "11", "Brandenburg": "12", "Mecklenburg-Vorpommern": "13",
        "Sachsen": "14", "Sachsen-Anhalt": "15", "Thüringen": "16"}
CITY_MARK = re.compile(r"\s*(\(Kreisfreie Stadt\)|, (Stadt|Stadtkreis|kreisfreie Stadt|Landeshauptstadt|"
                       r"Hansestadt|Wissenschaftsstadt|Klingenstadt|documenta-Stadt|Stadt der FernUniversität|"
                       r"Freie und Hansestadt))$")
LK_MARK = re.compile(r"^Landkreis\s+|\s*\(Landkreis\)$")
ALIAS = {"Oldenburg (Oldenburg)": "Oldenburg (Oldb)"}  # dataset base name -> VG250 GEN (explicit, audited)
CITY_BEZ = {"Kreisfreie Stadt", "Stadtkreis"}
LK_BEZ = {"Landkreis", "Kreis"}

BANDS = ["a20bis29", "a30bis39", "a40bis49", "a50bis59", "a60bis69", "a70bis79", "a80undaelter"]
EVER = {"Verheiratet", "Verwitwet", "Geschieden", "Eingetragene Lebenspartnerschaften",
        "Eingetr. Lebenspartner/-in verstorben", "Eingetragene Lebenspartnerschaft aufgehoben"}
DIV = {"Geschieden", "Eingetragene Lebenspartnerschaft aufgehoben"}
WID = {"Verwitwet", "Eingetr. Lebenspartner/-in verstorben"}


def norm(s: str) -> str:
    """Spacing/punctuation-insensitive key ('Dillingen a.d.Donau' == 'Dillingen a.d. Donau')."""
    return re.sub(r"[\s.\-()]", "", s).lower()


def match(names: list[tuple[str, str]], vg: list[dict]) -> dict[tuple[str, str], str]:
    by = defaultdict(list)
    for r in vg:
        by[(r["SN_L"], norm(r["GEN"]))].append(r)
    bases = defaultdict(set)  # (land, base) -> kinds seen in dataset
    parsed = {}
    for name, land in names:
        sn = LAND[land]
        if CITY_MARK.search(name):
            base, kind = CITY_MARK.sub("", name), "city"
        elif LK_MARK.search(name):
            base, kind = LK_MARK.sub("", name), "lk"
        else:
            base, kind = name, "plain"
        parsed[(name, land)] = (sn, base, kind)
        bases[(sn, base)].add(kind)
    out = {}
    for key, (sn, base, kind) in parsed.items():
        cands = by.get((sn, norm(ALIAS.get(base, base))), [])
        if len(cands) == 1:
            out[key] = cands[0]["AGS"]
            continue
        if len(cands) != 2:
            raise SystemExit(f"unmatched {key}: {len(cands)} candidates")
        kinds = bases[(sn, base)]
        if kind == "city" or (kind == "plain" and "lk" in kinds):
            want = CITY_BEZ
        elif kind == "lk" or (kind == "plain" and "city" in kinds):
            want = LK_BEZ
        else:
            raise SystemExit(f"ambiguous {key}: kinds {kinds}")
        pick = [r for r in cands if r["BEZ"] in want]
        if len(pick) != 1:
            raise SystemExit(f"ambiguous {key}: {[(r['GEN'], r['BEZ']) for r in cands]}")
        out[key] = pick[0]["AGS"]
    if len(set(out.values())) != len(out):
        raise SystemExit("non-injective Kreis mapping")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--vg", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    vg = gpd.read_file(a.vg, ignore_geometry=True)
    vg = vg[vg.GF == 4][["AGS", "GEN", "BEZ", "SN_L"]].to_dict("records")
    cols = ["uuid", "kreis", "bundesland", "age", "marital_status", "migration_background", "housing_tenure",
            "household_type"]
    acc = defaultdict(lambda: defaultdict(int))
    names = set()
    files = sorted(Path(a.data).glob("train-0000?.parquet"))
    assert len(files) == 10, files
    rows = []
    for f in files:
        t = pq.read_table(f, columns=cols).to_pydict()
        rows.append(t)
        names.update(zip(t["kreis"], t["bundesland"]))
    vocab = defaultdict(set)
    for t in rows:
        for c in ("marital_status", "migration_background", "housing_tenure", "household_type"):
            vocab[c].update(t[c])
    expect = {"marital_status": EVER | {"Ledig", "Ohne Angabe"},
              "migration_background": {"Mit Einwanderungsgeschichte", "Ohne Einwanderungsgeschichte"},
              "housing_tenure": {"Von Eigentümer/-in bewohnt", "Zu Wohnzwecken vermietet (auch mietfrei)"},
              "household_type": {"Einpersonenhaushalte (Singlehaushalte)", "Alleinerziehende Elternteile",
                                 "Mehrpersonenhaushalte ohne Kernfamilie", "Paare mit Kind(ern)", "Paare ohne Kind(er)"}}
    for c, e in expect.items():
        if vocab[c] != e:
            raise SystemExit(f"vocabulary mismatch in {c}: missing {sorted(e - vocab[c])}, unexpected {sorted(vocab[c] - e)}")
    m = match(sorted(names), vg)
    if len(m) != 400:
        raise SystemExit(f"{len(m)} Kreis names, expected 400")
    n = 0
    for t in rows:
        for i in range(len(t["uuid"])):
            ags = m[(t["kreis"][i], t["bundesland"][i])]
            h = int(t["uuid"][i][-1], 16) % 2
            for k in (f"{ags}|{h}",):
                c = acc[k]
                c["N"] += 1
                c["MIG_num"] += t["migration_background"][i] == "Mit Einwanderungsgeschichte"
                c["MIG_den"] += 1
                c["OWN_num"] += t["housing_tenure"][i] == "Von Eigentümer/-in bewohnt"
                c["OWN_den"] += 1
                ms = t["marital_status"][i]
                if ms in EVER:
                    c["DIV_den"] += 1
                    c["WID_den"] += 1
                    c["DIV_num"] += ms in DIV
                    c["WID_num"] += ms in WID
                c["SINGLE_num"] += t["household_type"][i] == "Einpersonenhaushalte (Singlehaushalte)"
                c["SINGLE_den"] += 1
                age = t["age"][i]
                if age >= 20:
                    c["OLD_den"] += 1
                    c["OLD_num"] += age >= 60
            # age band (Zensus 10-year bins from 20; ages 18-19 join the 20-29 band) x attribute counts
            band = BANDS[min(max(age, 20), 80) // 10 - 2]
            c = acc[f"{ags}|{h}"]
            c[f"N_{band}"] += 1
            for at, num_ok, den_ok in (("MIG", t["migration_background"][i] == "Mit Einwanderungsgeschichte", True),
                                       ("OWN", t["housing_tenure"][i] == "Von Eigentümer/-in bewohnt", True),
                                       ("DIV", ms in DIV, ms in EVER), ("WID", ms in WID, ms in EVER),
                                       ("SINGLE", t["household_type"][i] == "Einpersonenhaushalte (Singlehaushalte)", True)):
                if den_ok:
                    c[f"{at}_den_{band}"] += 1
                    c[f"{at}_num_{band}"] += num_ok
            n += 1
    fields = ["AGS", "half", "N"] + [f"{x}_{y}" for x in ("MIG", "OWN", "DIV", "WID", "SINGLE", "OLD") for y in ("num", "den")]
    fields += [f"N_{b}" for b in BANDS] + [f"{x}_{y}_{b}" for x in ("MIG", "OWN", "DIV", "WID", "SINGLE")
                                            for y in ("num", "den") for b in BANDS]
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for k in sorted(acc):
            ags, h = k.split("|")
            w.writerow({"AGS": ags, "half": h, **{f: acc[k].get(f, 0) for f in fields[2:]}})
    with open(Path(a.out).with_suffix(".map.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["kreis", "bundesland", "AGS"])
        for (k, l), ags in sorted(m.items()):
            w.writerow([k, l, ags])
    print(f"records {n}, kreise {len(m)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
