"""Rerun (d), descriptive only: gdaltransform and default pyproj for EPSG:6318 -> EPSG:10968 at 10 points (CPU Docker, --network none).
Points: 10 ids drawn with seed 134710 from the 30 re-queried frame points. Compared with committed NCAT beta A0 and with A1 (cs2cs 9.9.0)."""
import json, random, subprocess, sqlite3
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))
from analyze import dist_m
SCR = str(HERE / "scratch")  # scratch/pylib holds a pip install of pyproj 3.8.0 (PyPI wheel)
IMGS = {"gdal-latest": "ghcr.io/osgeo/gdal:ubuntu-small-latest", "gdal-3.12.0": "ghcr.io/osgeo/gdal:ubuntu-small-3.12.0"}
frame = {p["id"]: p for p in json.loads((HERE / "data" / "frame.json").read_text())}
a0 = {r["id"]: r for r in (json.loads(l) for l in (HERE / "out" / "ncat_a0.jsonl").read_text().splitlines() if l.strip())}
a1 = json.loads((HERE / "out" / "arms.json").read_text())["A1"]["res"]
req = [json.loads(l)["id"] for l in (HERE / "rerun" / "ncat_requery.jsonl").read_text().splitlines()]
ids = random.Random(134710).sample(req, 10)
def run(img, cmd, stdin=None, env=()):
    base = ["docker", "run", "-i", "--rm", "--network", "none", "--memory", "1g"] + [x for e in env for x in ("-e", e)]
    p = subprocess.run(base + [img] + cmd, input=stdin, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout, p.stderr
res = {"ids": ids, "engines": {}}
for name, img in IMGS.items():
    ver = run(img, ["gdalinfo", "--version"])[1].strip()
    csv = run(img, ["cs2cs"])[2].splitlines()[0] if True else ""
    meta = run(img, ["python3", "-c", "import sqlite3;c=sqlite3.connect('file:/usr/share/proj/proj.db?mode=ro',uri=True);print(dict(c.execute(\"select key,value from metadata where key in ('EPSG.VERSION','PROJ.VERSION')\")))"])[1].strip()
    stdin = "".join(f"{frame[i]['lon']} {frame[i]['lat']}\n" for i in ids)   # gdaltransform: x y = lon lat (traditional GIS order)
    rc, so, se = run(img, ["gdaltransform", "-s_srs", "EPSG:6318", "-t_srs", "EPSG:10968"], stdin)
    rc2, so2, se2 = run(img, ["cs2cs", "-d", "10", "EPSG:6318", "EPSG:10968"], "".join(f"{frame[i]['lat']} {frame[i]['lon']}\n" for i in ids))
    pi = run(img, ["projinfo", "-s", "EPSG:6318", "-t", "EPSG:10968", "--summary"])[1].strip().splitlines()
    res["engines"][name] = {"image": img, "gdal": ver, "cs2cs_banner": csv, "proj_db": meta, "gdaltransform_rc": rc, "gdaltransform_stderr": se.strip()[:500],
                            "gdaltransform_out": so.splitlines(), "cs2cs_rc": rc2, "cs2cs_stderr": se2.strip()[:500], "cs2cs_out": so2.splitlines(), "projinfo_default": pi}
py = r"""
import sys, json; sys.path.insert(0, '/pylib')
import pyproj; from pyproj import Transformer; from pyproj.database import get_database_metadata as m
ids = json.loads(sys.argv[1]); t = Transformer.from_crs(6318, 10968)
out = [t.transform(lat, lon) for lat, lon in ids]
print(json.dumps({"pyproj": pyproj.__version__, "proj": pyproj.proj_version_str, "epsg": m("EPSG.VERSION"), "desc": t.description, "accuracy": t.accuracy,
                  "ops": [str(o.name) for o in t.operations] if t.operations else None, "out": out, "warnings": None}))
"""
rc, so, se = run("python:3.12-slim", ["python", "-I", "-c", py, json.dumps([[frame[i]["lat"], frame[i]["lon"]] for i in ids])])
# pyproj is a PyPI wheel installed into SCR/pylib on the host (public dependency fetch), mounted read-only
p = subprocess.run(["docker", "run", "--rm", "--network", "none", "--memory", "1g", "-v", f"{SCR}/pylib:/pylib:ro", "python:3.12-slim", "python", "-I", "-c", py,
                    json.dumps([[frame[i]["lat"], frame[i]["lon"]] for i in ids])], capture_output=True, text=True, timeout=300)
res["pyproj"] = json.loads(p.stdout) if p.returncode == 0 else {"rc": p.returncode, "stderr": p.stderr[:500]}
res["pyproj_stderr"] = p.stderr.strip()[:500]
def d_to(i, lat, lon, ref):
    return dist_m(ref[0], ref[1], lat, lon)[0]
rows = []
for k, i in enumerate(ids):
    o = a0[i]; ref = (o["out_lat"], o["out_lon"]); r = {"id": i, "name": frame[i]["name"], "state": frame[i]["state"], "lat": frame[i]["lat"], "lon": frame[i]["lon"], "ncat": ref}
    r["cs2cs_9.9.0_vs_ncat_m"] = d_to(i, a1[i]["lat"], a1[i]["lon"], ref)
    for name, e in res["engines"].items():
        g = e["gdaltransform_out"][k].split(); r[f"gdaltransform[{name}]"] = (float(g[1]), float(g[0]))      # (lat, lon)
        r[f"gdaltransform[{name}]_vs_ncat_m"] = d_to(i, float(g[1]), float(g[0]), ref)
        c = e["cs2cs_out"][k].split(); r[f"cs2cs[{name}]_vs_ncat_m"] = d_to(i, float(c[0]), float(c[1]), ref)
    pl = res["pyproj"]["out"][k]; r["pyproj"] = pl; r["pyproj_vs_ncat_m"] = d_to(i, pl[0], pl[1], ref)
    rows.append(r)
res["rows"] = rows
(HERE / "rerun" / "descriptive_d.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1)[:4000])
for r in rows:
    print(r["id"], r["state"], "A1 %.3f" % r["cs2cs_9.9.0_vs_ncat_m"], *("%s %.3f" % (k.split("]")[0].split("[")[0] + (k.split("[")[1].split("]")[0] if "[" in k else ""), r[k]) for k in r if k.endswith("_vs_ncat_m") and k != "cs2cs_9.9.0_vs_ncat_m"))
