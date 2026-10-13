"""Seeded frame: Census 2025 county internal points (CONUS sample + all Alaska)."""
import csv, json, random, sys, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
SRC = HERE / "data" / "2025_Gaz_counties_national.txt"
NOT_CONUS = {"AK", "HI", "PR", "GU", "VI", "AS", "MP"}
def main():
    rows = list(csv.DictReader(SRC.open(encoding="utf-8"), delimiter="|"))
    rows = [{k.strip(): v.strip() for k, v in r.items()} for r in rows]
    conus = sorted([r for r in rows if r["USPS"] not in NOT_CONUS], key=lambda r: r["GEOID"])
    ak = sorted([r for r in rows if r["USPS"] == "AK"], key=lambda r: r["GEOID"])
    rng = random.Random(13462)
    pick = rng.sample(conus, 200)
    pts = []
    for stratum, rs in (("CONUS", sorted(pick, key=lambda r: r["GEOID"])), ("AK", ak)):
        for r in rs:
            pts.append({"id": r["GEOID"], "state": r["USPS"], "name": r["NAME"], "stratum": stratum,
                        "lat": round(float(r["INTPTLAT"]), 6), "lon": round(float(r["INTPTLONG"]), 6)})
    out = HERE / "data" / "frame.json"
    out.write_text(json.dumps(pts, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(len(pts), sum(p["stratum"] == "AK" for p in pts), hashlib.sha256(out.read_bytes()).hexdigest())
if __name__ == "__main__":
    main()
