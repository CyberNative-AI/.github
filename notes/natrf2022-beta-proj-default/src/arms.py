"""PROJ arms in CPU Docker (--network none), osgeo/proj:9.9.0.
A1 stock default 2D: EPSG:6318 -> EPSG:10968 (no epoch)
A2 stock 3D with epoch: EPSG:6319 -> EPSG:10967, input epoch 2010.0
A3 community aux DB grid path: EPSG:6318 -> NSRS:NATRF2022_2D (NSRS-2022-PROJ @AUX_COMMIT)
S3 SPCS2022: NCAT's own NATRF2022 output -> NSRS:<zone> projected (aux DB), compared with NCAT SPC N/E."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
IMAGE = "osgeo/proj:9.9.0"
AUX = HERE / "NSRS-2022-PROJ"  # a clone of NSRS-2022-PROJ checked out at AUX_COMMIT
AUX_COMMIT = "1b7e33d9739680d6b1f61991371fc84a9e7f38fd"
def docker(args, stdin, aux=False):
    cmd = ["docker", "run", "-i", "--rm", "--network", "none", "--memory", "1g"]
    if aux:
        cmd += ["-v", f"{AUX}:/aux:ro", "-e", "PROJ_AUX_DB=/aux/nsrs_proj.db", "-e", "PROJ_DATA=/usr/share/proj:/aux"]
    p = subprocess.run(cmd + [IMAGE] + args, input=stdin, capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout, p.stderr
def run_arm(name, args, pts, fmt, aux=False):
    rc, so, se = docker(["cs2cs", "-d", "10"] + args, "".join(fmt(p) for p in pts), aux)
    lines = so.splitlines()
    assert rc == 0 and len(lines) == len(pts), (name, rc, len(lines), len(pts), se[:500])
    res = {}
    for p, l in zip(pts, lines):
        v = l.split()
        try:
            res[p["id"]] = {"lat": float(v[0]), "lon": float(v[1]), "raw": l}
        except Exception:
            res[p["id"]] = {"lat": None, "lon": None, "raw": l}
    return {"arm": name, "args": args, "rc": rc, "n_lines": len(lines), "n_pts": len(pts), "stderr": se[:4000], "res": res}
def main():
    git = subprocess.run(["git", "-C", str(AUX), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert git == AUX_COMMIT, git
    pts = json.loads((HERE / "data" / "frame.json").read_text())
    out = {"image": IMAGE, "aux_commit": git}
    out["A1"] = run_arm("A1", ["EPSG:6318", "EPSG:10968"], pts, lambda p: f"{p['lat']} {p['lon']}\n")
    out["A2"] = run_arm("A2", ["EPSG:6319", "EPSG:10967"], pts, lambda p: f"{p['lat']} {p['lon']} 0 2010.0\n")
    out["A3"] = run_arm("A3", ["EPSG:6318", "NSRS:NATRF2022_2D"], pts, lambda p: f"{p['lat']} {p['lon']}\n", aux=True)
    for s, t, a in (("EPSG:6318", "EPSG:10968", False), ("EPSG:6319", "EPSG:10967", False), ("EPSG:6318", "NSRS:NATRF2022_2D", True)):
        out.setdefault("projinfo", []).append({"s": s, "t": t, "aux": a, "summary": docker(["projinfo", "-s", s, "-t", t, "--summary"], "", a)[1],
                                               "summary_intersects": docker(["projinfo", "-s", s, "-t", t, "--spatial-test", "intersects", "--summary"], "", a)[1]})
    # S3: SPCS2022 projection of NCAT's own output, per NCAT-reported zone
    a0 = [json.loads(l) for l in (HERE / "out" / "ncat_a0.jsonl").read_text().splitlines() if l.strip()]
    s3 = {}
    for r in a0:
        if r.get("status") != "VALID" or not r.get("spc_zone") or r.get("spc_n") in (None, "N/A") or r.get("spc_zone", "").startswith("N/A"):
            continue
        code = r["spc_zone"].split("-")[0].strip().replace(" ", "_")
        rc, so, se = docker(["cs2cs", "-d", "4", "NSRS:NATRF2022_2D", f"NSRS:{code}"], f"{r['out_lat']} {r['out_lon']}\n", True)
        v = so.split()
        s3[r["id"]] = {"zone_label": r["spc_zone"], "code": code, "rc": rc, "raw": so.strip(), "stderr": se.strip()[:300],
                       "n": float(v[0]) if len(v) >= 2 and v[0] != "*" else None, "e": float(v[1]) if len(v) >= 2 and v[0] != "*" else None}
    out["S3"] = s3
    out["S3_axis_check"] = docker(["projinfo", "NSRS:PA_W", "-o", "WKT2_2019", "-q"], "", True)[1][-600:]
    (HERE / "out" / "arms.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print({k: (v["rc"], v["n_lines"]) for k, v in out.items() if k in ("A1", "A2", "A3")}, len(s3))
if __name__ == "__main__":
    main()
