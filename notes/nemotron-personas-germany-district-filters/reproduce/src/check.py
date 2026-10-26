"""Recount of the note's numbers from out/ref_kreis.csv and out/ds_kreis.csv. Python standard library only.

Prints, per attribute, the Spearman rank correlation and the OLS slope of the dataset's district rate on the census
district rate (400 districts, unweighted), then the immigration-history comparisons, and writes
out/immigration-by-district.csv.

Census side (Zensus 2022 1 km grid, all ages): share born abroad. Dataset side (adults, 18+): share
'Mit Einwanderungsgeschichte'. Two bounds compare people aged 20 or over on both sides:
- census_max_born_abroad_20plus: (people born abroad in usable birth-table cells + every person in the district's
  other cells) / people aged 20+ in usable age-table cells. It counts every person born abroad, of any age, and every
  person whose birth country is suppressed, as a person aged 20+ born abroad, and divides by a count of people aged
  20+ that leaves out suppressed cells, so the born-abroad share among the district's people aged 20+ cannot be
  higher (apart from Destatis's confidentiality changes to grid cells). The district is the set of grid cells
  assigned to it by cell centre.
- dataset_min_immigration_history_20plus: (records with immigration history - records aged 18-19) / records aged
  20+. It assumes every 18- or 19-year-old record has an immigration history, so the share among records aged 20+
  cannot be lower.

Usage: python3 -I check.py out
"""
import csv
import statistics as st
import sys
from pathlib import Path

EAST = {"12", "13", "14", "15", "16"}  # Brandenburg, Mecklenburg-Vorpommern, Sachsen, Sachsen-Anhalt, Thüringen
LAND = {"01": "Schleswig-Holstein", "02": "Hamburg", "03": "Niedersachsen", "04": "Bremen",
        "05": "Nordrhein-Westfalen", "06": "Hessen", "07": "Rheinland-Pfalz", "08": "Baden-Württemberg",
        "09": "Bayern", "10": "Saarland", "11": "Berlin", "12": "Brandenburg", "13": "Mecklenburg-Vorpommern",
        "14": "Sachsen", "15": "Sachsen-Anhalt", "16": "Thüringen"}


def ranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def pearson(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return num / (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5


def slope(x, y):
    mx, my = st.mean(x), st.mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)


def main(out):
    ref = {r["AGS"]: r for r in csv.DictReader(open(out / "ref_kreis.csv", encoding="utf-8"))}
    ds = {}
    for r in csv.DictReader(open(out / "ds_kreis.csv", encoding="utf-8")):
        d = ds.setdefault(r["AGS"], {})
        for k, v in r.items():
            if k not in ("AGS", "half"):
                d[k] = d.get(k, 0.0) + float(v)
    ags = sorted(ref)
    print(f"districts {len(ags)}, dataset records {int(sum(ds[a]['N'] for a in ags))}")
    for k in ("OWN", "DIV", "WID", "OLD", "SINGLE", "MIG"):
        z = [float(ref[a][k + "_num"]) / float(ref[a][k + "_den"]) for a in ags]
        d = [ds[a][k + "_num"] / ds[a][k + "_den"] for a in ags]
        print(f"{k:6} rho {pearson(ranks(z), ranks(d)):.3f}  slope {slope(z, d):.3f}  "
              f"census {min(z):.3f}-{max(z):.3f}  dataset {min(d):.3f}-{max(d):.3f}")

    rows = []
    for a in ags:
        r = ref[a]
        born_abroad = float(r["MIG_num"]) / float(r["MIG_den"])
        census_max = (float(r["MIG_num"]) + max(0.0, float(r["pop_all"]) - float(r["MIG_covpop"]))) / float(r["OLD_den"])
        dataset = ds[a]["MIG_num"] / ds[a]["MIG_den"]
        aged_18_19 = ds[a]["N"] - ds[a]["OLD_den"]
        dataset_min = max(0.0, ds[a]["MIG_num"] - aged_18_19) / ds[a]["OLD_den"]
        rows.append({"ags": a, "district": r["GEN"], "type": r["BEZ"], "land": LAND[r["SN_L"]],
                     "east": int(r["SN_L"] in EAST), "census_born_abroad_all_ages": round(born_abroad, 4),
                     "census_max_born_abroad_20plus": round(census_max, 4),
                     "dataset_immigration_history_18plus": round(dataset, 4),
                     "dataset_min_immigration_history_20plus": round(dataset_min, 4),
                     "dataset_records": int(ds[a]["MIG_den"])})
    east = [r for r in rows if r["east"]]
    west = [r for r in rows if not r["east"]]
    nat_z = sum(float(ref[a]["MIG_num"]) for a in ags) / sum(float(ref[a]["MIG_den"]) for a in ags)
    nat_d = sum(ds[a]["MIG_num"] for a in ags) / sum(ds[a]["MIG_den"] for a in ags)
    print(f"national: census born abroad {nat_z:.3f}, dataset {nat_d:.3f}")
    for name, grp in (("east (75 expected)", east), ("west and Berlin", west)):
        print(f"{name}: n {len(grp)}, median census {st.median(r['census_born_abroad_all_ages'] for r in grp):.3f}, "
              f"median census max 20+ {st.median(r['census_max_born_abroad_20plus'] for r in grp):.3f}, "
              f"median dataset {st.median(r['dataset_immigration_history_18plus'] for r in grp):.3f}, "
              f"median dataset min 20+ {st.median(r['dataset_min_immigration_history_20plus'] for r in grp):.3f}")
    print("east districts with dataset above census:",
          sum(r["dataset_immigration_history_18plus"] > r["census_born_abroad_all_ages"] for r in east),
          "; dataset min 20+ above census max 20+:",
          sum(r["dataset_min_immigration_history_20plus"] > r["census_max_born_abroad_20plus"] for r in east),
          "; not above:", [r["district"] for r in east
                           if r["dataset_min_immigration_history_20plus"] <= r["census_max_born_abroad_20plus"]])
    by = sorted(rows, key=lambda r: r["census_born_abroad_all_ages"])
    for r in by[:5] + by[-8:]:
        print(f"  {r['district']} ({r['type']}): census {r['census_born_abroad_all_ages']:.3f}, "
              f"census max 20+ {r['census_max_born_abroad_20plus']:.3f}, "
              f"dataset {r['dataset_immigration_history_18plus']:.3f}, "
              f"dataset min 20+ {r['dataset_min_immigration_history_20plus']:.3f}, "
              f"n {r['dataset_records']}")
    with open(out / "immigration-by-district.csv", "w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
