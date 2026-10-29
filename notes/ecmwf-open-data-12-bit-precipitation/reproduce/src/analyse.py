"""Analysis (runs in the img/Dockerfile image, network none). Usage: analyse.py RAWDIR OUTJSON
Pre-change runs: decode 16-bit tp; SIM = ecCodes re-encode at bitsPerValue=12 (consistent rounding: LOWER bound on flips);
SIM_DITHER = nonzero ORIG values + independent U(-q16/2,q16/2) dither per message, then the same 12-bit grid (UPPER bound).
Post-change run: real-data arm (descriptive). Gates and verdict computed here (PROTOCOL.md)."""
import json, sys, pathlib, collections
import numpy as np
import eccodes as ec

PRE, POST = ["20261015", "20261019"], ["20261028"]
THR01, THR1 = 1e-4, 1e-3          # > 0.1 mm (Open-Meteo PoP), > 1.0 mm (contrast above one 12-bit quantum)
raw, outp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
rng = np.random.default_rng(17504)
G = collections.Counter(); FAIL = []

def msgs(path):
    with open(path, "rb") as f:
        while (h := ec.codes_grib_new_from_file(f)) is not None: yield h

def g(h, k, default=None):
    try: return ec.codes_get(h, k)
    except Exception: return default

def info(h):
    return dict(param=g(h, "shortName"), number=g(h, "number", 0), type=g(h, "dataType"), E=g(h, "binaryScaleFactor"),
                D=g(h, "decimalScaleFactor"), nbits=g(h, "bitsPerValue"), ref=float(g(h, "referenceValue")), packing=g(h, "packingType"),
                npts=g(h, "numberOfValues"))

def reencode(h, nbits):
    # AMENDMENT-01: setting bitsPerValue alone leaves CCSDS data undecodable; re-set the values to repack
    c = ec.codes_clone(h); v0 = ec.codes_get_values(h); ec.codes_set_long(c, "bitsPerValue", nbits); ec.codes_set_values(c, v0)
    v = ec.codes_get_values(c); i = info(c); ec.codes_release(c); return v, i

def q_halfup(x, ref, E):
    s = 2.0 ** E; return np.floor((x - ref) / s + 0.5) * s + ref

def load_step(date, stream, step, L, sim):
    """returns dict number -> (orig, sim, sim_dither) restricted to land; plus meta"""
    out, meta = {}, []
    for h in msgs(raw / date / stream / f"{step}.grib2"):
        i = info(h)
        if i["param"] == "lsm": ec.codes_release(h); continue
        assert i["param"] == "tp", i
        v = ec.codes_get_values(h); assert v.size == L.size, (v.size, L.size)
        m = dict(step=step, number=i["number"], E=i["E"], nbits=i["nbits"], ref=i["ref"], packing=i["packing"], max=float(v.max()))
        if sim:
            v16, i16 = reencode(h, i["nbits"])                                   # G1 identity
            G["g1_n"] += 1; G["g1_ok"] += int(np.array_equal(v16, v) and i16["E"] == i["E"])
            v12, i12 = reencode(h, 12)
            ok = i12["nbits"] == 12 and (v.max() == 0 or (i12["E"] - i["E"] in (4, 5) and np.max(np.abs(v12 - v)) > 0))
            G["sim12_n"] += 1; G["sim12_ok"] += int(ok)                            # SIM really repacked
            G["g1b_n"] += 1; G["g1b_ok"] += int(np.array_equal(q_halfup(v, i12["ref"], i12["E"]), v12))  # numpy rule == ecCodes on this input
            if i["nbits"] == 16 and v.max() > 0:                                   # off-grid half-up check: v + small noise
                noise = v + rng.uniform(-0.4, 0.4, v.size) * 2.0 ** i["E"]
                c = ec.codes_clone(h); ec.codes_set_long(c, "bitsPerValue", 12); ec.codes_set_values(c, np.maximum(noise, 0))
                vn, iN = ec.codes_get_values(c), info(c); ec.codes_release(c)
                G["g1c_n"] += 1; G["g1c_ok"] += int(np.allclose(q_halfup(np.maximum(noise, 0), iN["ref"], iN["E"]), vn, rtol=0, atol=2.0 ** iN["E"] * 1e-6))
            q16 = 2.0 ** i["E"]; nz = v > 0
            vd = np.where(nz, np.maximum(v + rng.uniform(-0.5, 0.5, v.size) * q16, 0.0), 0.0)
            vd12 = q_halfup(vd, i12["ref"], i12["E"])
            m.update(E12=i12["E"], ref12=i12["ref"], ties=int(np.count_nonzero(np.mod((v - i12["ref"]) / 2.0 ** i12["E"], 1.0) == 0.5)))
            out[i["number"]] = (v[L], v12[L], vd12[L])
        else:
            vr, ir = reencode(h, 12)                                               # G2 consistency (weak; see protocol)
            G["g2_n"] += 1; G["g2_ok"] += int(np.array_equal(vr, v) and ir["E"] == i["E"])
            out[i["number"]] = (v[L],)
        meta.append(m); ec.codes_release(h)
    return out, meta

def lsm_of(date):
    for h in msgs(raw / date / "oper" / "0.grib2"):
        if g(h, "shortName") == "lsm": v = ec.codes_get_values(h); ec.codes_release(h); return v > 0.5
        ec.codes_release(h)
    raise SystemExit("no lsm")

ARMS = ("sim", "dither")
def ens_arm(date, L, sim):
    prev = None; acc = collections.Counter(); win = []; hist = collections.Counter(); meta = []
    for st in range(0, 145, 6):
        d, mm = load_step(date, "enfo", st, L, sim); meta += mm
        keys = sorted(d); assert keys == list(range(1, 51)), (date, st, keys[:3], len(keys))
        cur = [np.stack([d[k][j] for k in keys]) for j in range(len(d[keys[0]]))]
        if prev is not None:
            Ao = cur[0] - prev[0]
            acc["member_windows"] += Ao.size; acc["neg_orig"] += int(np.count_nonzero(Ao < 0))
            if sim:
                w = {"end_step": st}
                for j, arm in ((1, "sim"), (2, "dither")):
                    As = cur[j] - prev[j]; acc[f"neg_{arm}"] += int(np.count_nonzero(As < 0))
                    for tn, thr in (("01", THR01), ("1", THR1)):
                        Po, Ps = (Ao > thr).mean(0), (As > thr).mean(0); dP = Ps - Po
                        unc = ((Po > 0) & (Po < 1)) | ((Ps > 0) & (Ps < 1))
                        k = f"{arm}_{tn}"
                        acc[k + "_all_n"] += dP.size; acc[k + "_all_ge10"] += int(np.count_nonzero(np.abs(dP) >= 0.0999))
                        acc[k + "_unc_n"] += int(unc.sum()); acc[k + "_unc_ge10"] += int(np.count_nonzero(np.abs(dP[unc]) >= 0.0999))
                        acc[k + "_unc_ge20"] += int(np.count_nonzero(np.abs(dP[unc]) >= 0.1999))
                        w[k + "_unc_n"] = int(unc.sum()); w[k + "_unc_sum_dP"] = float(dP[unc].sum())
                        w[k + "_unc_ge10"] = int(np.count_nonzero(np.abs(dP[unc]) >= 0.0999))
                        if arm == "sim" and tn == "01":
                            for b in np.round(dP[dP != 0], 2): hist[f"{b:+.2f}"] += 1
                # mechanism: share of ORIG wet(>0.1mm) member-windows with amount below one 12-bit quantum
                q12 = 2.0 ** max(x["E12"] for x in mm)
                acc["orig_wet01"] += int(np.count_nonzero(Ao > THR01)); acc["orig_wet01_below_q12"] += int(np.count_nonzero((Ao > THR01) & (Ao < q12)))
                win.append(w)
        else:
            Ao = None
        prev = cur
    return dict(acc=dict(acc), windows=win, dP_hist_sim01=dict(sorted(hist.items())), meta=meta)

def oper_arm(date, L, sim):
    steps = list(range(0, 145, 6)) + list(range(150, 361, 6)); V = {}; meta = []
    for st in steps:
        d, mm = load_step(date, "oper", st, L, sim); meta += mm
        assert len(d) == 1, (date, st, list(d)); V[st] = next(iter(d.values()))
    acc = collections.Counter()
    def windows(span, last):
        for t in range(span, last + 1, span): yield t
    for span, last in ((6, 144), (24, 360)):
        for t in windows(span, last):
            Ao = V[t][0] - V[t - span][0]; acc[f"w{span}_n"] += Ao.size; acc[f"w{span}_neg_orig"] += int(np.count_nonzero(Ao < 0))
            acc[f"w{span}_wet01_orig"] += int(np.count_nonzero(Ao > THR01))
            if sim:
                for j, arm in ((1, "sim"), (2, "dither")):
                    As = V[t][j] - V[t - span][j]
                    acc[f"w{span}_{arm}_neg"] += int(np.count_nonzero(As < 0))
                    acc[f"w{span}_{arm}_flip01"] += int(np.count_nonzero((Ao > THR01) != (As > THR01)))
                    acc[f"w{span}_{arm}_flip1"] += int(np.count_nonzero((Ao > THR1) != (As > THR1)))
                    acc[f"w{span}_{arm}_maxabs_mm"] = max(acc[f"w{span}_{arm}_maxabs_mm"], float(np.max(np.abs(As - Ao)) * 1000))
    return dict(acc=dict(acc), meta=meta)

R = {"pre": {}, "post": {}}
for dte in PRE + POST:
    sim = dte in PRE; L = lsm_of(dte)
    R["pre" if sim else "post"][dte] = dict(land_points=int(L.sum()), oper=oper_arm(dte, L, sim), enfo=ens_arm(dte, L, sim))
    print("done", dte, flush=True)

# ---- gates and verdict (frozen in PROTOCOL.md) ----
gates = dict(G)
gate_ok = dict(G1=G["g1_ok"] == G["g1_n"] > 0, SIM12=G["sim12_ok"] == G["sim12_n"] > 0, G1b=G["g1b_ok"] == G["g1b_n"] > 0,
               G1c=G["g1c_ok"] == G["g1c_n"] > 0, G2=G["g2_n"] > 0 and G["g2_ok"] >= 0.99 * G["g2_n"])
def rate(a, k): return a[k + "_unc_ge10"] / max(a[k + "_unc_n"], 1)
per_run = {}
for dte in PRE:
    e, o = R["pre"][dte]["enfo"]["acc"], R["pre"][dte]["oper"]["acc"]
    per_run[dte] = dict(P1_sim=rate(e, "sim_01"), P1_dither=rate(e, "dither_01"), P1c_sim=rate(e, "sim_1"), P1c_dither=rate(e, "dither_1"),
                        P3_sim=o["w6_sim_flip01"] / max(o["w6_wet01_orig"], 1), P3_dither=o["w6_dither_flip01"] / max(o["w6_wet01_orig"], 1))
# bias: mean signed dP on uncertain set, bootstrap over windows (both runs pooled), SIM arm, 0.1 mm
W = [w for dte in PRE for w in R["pre"][dte]["enfo"]["windows"]]
S = np.array([w["sim_01_unc_sum_dP"] for w in W]); N = np.array([w["sim_01_unc_n"] for w in W])
b = [S[ix].sum() / max(N[ix].sum(), 1) for ix in (rng.integers(0, len(W), len(W)) for _ in range(2000))]
bias = dict(mean=float(S.sum() / max(N.sum(), 1)), ci95=[float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))])
if not (gate_ok["G1"] and gate_ok["SIM12"]): verdict = "STOP_INSTRUMENT"
elif not gate_ok["G2"]: verdict = "INCONCLUSIVE"
elif all(per_run[d]["P1_sim"] >= 0.05 or per_run[d]["P3_sim"] >= 0.05 for d in PRE): verdict = "CLAIM_CONTRADICTED"
elif all(per_run[d]["P1_dither"] < 0.005 and per_run[d]["P3_dither"] < 0.005 for d in PRE): verdict = "CLAIM_HOLDS"
else: verdict = "MIXED"
R.update(gates=gates, gate_ok=gate_ok, per_run=per_run, bias_sim01=bias, verdict=verdict)
outp.write_text(json.dumps(R, indent=1)); print("VERDICT", verdict, json.dumps(per_run), json.dumps(gate_ok), json.dumps(bias))
