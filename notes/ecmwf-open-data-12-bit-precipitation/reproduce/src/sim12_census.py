"""SIM12 failure census: re-apply the frozen SIM12 predicate (analyse.py line 49, AMENDMENT-01 reencode) per message; list every failure."""
import json, sys, pathlib, collections
import numpy as np, eccodes as ec
raw = pathlib.Path("/raw"); out = []; C = collections.Counter()
def reencode(h, nbits):
    c = ec.codes_clone(h); v0 = ec.codes_get_values(h); ec.codes_set_long(c, "bitsPerValue", nbits); ec.codes_set_values(c, v0)
    v = ec.codes_get_values(c); r = (ec.codes_get(c, "bitsPerValue"), ec.codes_get(c, "binaryScaleFactor")); ec.codes_release(c); return v, r
for date in ("20261015", "20261019"):
    for stream, steps in (("oper", list(range(0, 145, 6)) + list(range(150, 361, 6))), ("enfo", list(range(0, 145, 6)))):
        for st in steps:
            with open(raw / date / stream / f"{st}.grib2", "rb") as f:
                while (h := ec.codes_grib_new_from_file(f)) is not None:
                    if ec.codes_get(h, "shortName") != "tp": ec.codes_release(h); continue
                    v = ec.codes_get_values(h); E = ec.codes_get(h, "binaryScaleFactor"); n0 = ec.codes_get(h, "bitsPerValue")
                    v12, (n12, E12) = reencode(h, 12)
                    ok = n12 == 12 and (v.max() == 0 or (E12 - E in (4, 5) and np.max(np.abs(v12 - v)) > 0))
                    zero = bool(v.max() == 0)
                    C[("ok" if ok else "fail", "zero" if zero else "nonzero")] += 1
                    if not ok: out.append(dict(date=date, stream=stream, step=st, number=(ec.codes_get(h, "number") if ec.codes_is_defined(h, "number") else 0), nbits_orig=n0, nbits12=n12, E=E, E12=E12, vmax=float(v.max()), vmin=float(v.min()), all_equal_to_orig=bool(np.array_equal(v12, v))))
                    ec.codes_release(h)
print(json.dumps(dict(counts={"/".join(k): n for k, n in sorted(C.items())}, failures=out), indent=1))
