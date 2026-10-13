"""Distinct cases = (argv, piped_in) over both strata, x fixture modes A (bare) and B (materialized+rerooted),
plus positive controls (differences reported in uutils/coreutils#15254, adapted to the fixture)."""
import json, hashlib, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTROLS = [["split", "--numeric-suffixes=1", "-d", "f1.txt"], ["stat", "--printf=x", "-c", "%n", "f2.txt"],
            ["readlink", "-e", "-f", "missing.txt"], ["ls", "--file-type", "--classify=auto"],
            ["realpath", "--no-symlinks", "--logical", "link1"], ["sum", "--sysv", "-r", "f1.txt"]]
def cid(argv, piped, mode):
    return hashlib.sha256(json.dumps([argv, piped, mode]).encode()).hexdigest()[:16]
def main(out, *srcs):
    seen = {}
    for s in srcs:
        for l in open(ROOT / "data" / s):
            r = json.loads(l)
            for mode in ("A", "B"):
                k = cid(r["argv"], r["piped_in"], mode)
                seen.setdefault(k, {"id": k, "argv": r["argv"], "piped_in": r["piped_in"], "mode": mode, "control": False})
    for a in CONTROLS:
        k = cid(a, False, "C")
        seen[k] = {"id": k, "argv": a, "piped_in": False, "mode": "A", "control": True}
    rows = sorted(seen.values(), key=lambda r: r["id"])
    pathlib.Path(out).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    print(len(rows), file=sys.stderr)
if __name__ == "__main__":
    main(*sys.argv[1:])
