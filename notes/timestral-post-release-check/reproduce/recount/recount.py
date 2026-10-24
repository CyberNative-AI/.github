"""Independent recount of the headline ratios from score-all.json per_series (stdlib only)."""
import json, math, random, sys
d = json.load(open(sys.argv[1]))
def gm(xs): return math.exp(sum(math.log(x) for x in xs)/len(xs))
def ratio(arm, a, b, boot=True):
    ps = d[arm]["per_series"]; sids = sorted(ps[a])
    r = [math.log(ps[a][s][0]/ps[b][s][0]) for s in sids]
    pt = math.exp(sum(r)/len(r))
    rnd = random.Random(7); bs = sorted(sum(rnd.choice(r) for _ in r)/len(r) for _ in range(4000))
    return pt, math.exp(bs[int(0.025*4000)]), math.exp(bs[int(0.975*4000)-1]), len(r)
pairs = {"FRESH/E": [("Timestral-209M","Chronos-2"),("Timestral-209M","TimesFM-2.5"),("Timestral-209M","MSTL"),("Timestral-209M","AutoETS"),("Timestral-209M","SeasonalNaive"),("Timestral-5M","Timestral-209M"),("Timestral-28M","Chronos-2-small"),("Timestral-209M","EIA-BA-forecast")],
         "FRESH/W": [("Timestral-209M","Chronos-2"),("Timestral-209M","TimesFM-2.5"),("Timestral-209M","AutoETS"),("Timestral-209M","AutoARIMA"),("Timestral-209M","SeasonalNaive"),("Timestral-5M","Timestral-209M"),("Timestral-28M","Chronos-2-small")],
         "PRE/E": [("Timestral-209M","Chronos-2")], "PRE/W": [("Timestral-209M","Chronos-2")]}
bad = 0
for arm, pl in pairs.items():
    for a,b in pl:
        pt, lo, hi, n = ratio(arm, a, b); s = d[arm]["pairs"][f"{a}/{b}"]
        ok = abs(pt-s["ratio"])<1e-9 and abs(lo-s["lo"])<0.01 and abs(hi-s["hi"])<0.01 and n==s["n"]
        bad += not ok
        print(f"{arm:8} {a}/{b:16} recount {pt:.3f} [{lo:.3f},{hi:.3f}] n={n} | scorer {s['ratio']:.3f} [{s['lo']:.3f},{s['hi']:.3f}] {'OK' if ok else 'DIFF'}")
for arm in ("FRESH/E","FRESH/W"):
    ps = d[arm]["per_series"]; sn = ps["SeasonalNaive"]; sids = sorted(sn)
    for m in ps:
        g = gm([ps[m][s][0]/sn[s][0] for s in sids]); a = sum(ps[m][s][0] for s in sids)/len(sids)
        t = d[arm]["table"][m]; ok = abs(g-t["gmean_rel_mase"])<1e-9 and abs(a-t["mean_mase"])<1e-9; bad += not ok
        print(f"{arm:8} {m:16} gmean_rel {g:.3f} mean_mase {a:.3f} wall {t['wall_s']} {'OK' if ok else 'DIFF'}")
for dom in "EW":
    pre, fr = d[f"PRE/{dom}"]["per_series"], d[f"FRESH/{dom}"]["per_series"]; sids = sorted(pre["Timestral-209M"])
    x = [math.log(pre["Timestral-209M"][s][0]/pre["Chronos-2"][s][0]) - math.log(fr["Timestral-209M"][s][0]/fr["Chronos-2"][s][0]) for s in sids]
    rnd = random.Random(7); bs = sorted(sum(rnd.choice(x) for _ in x)/len(x) for _ in range(4000))
    s = d[f"LEAKPROBE/{dom}"]["Chronos-2"]
    print(f"DiD {dom} recount {math.exp(sum(x)/len(x)):.3f} [{math.exp(bs[100]):.3f},{math.exp(bs[3899]):.3f}] | scorer {s['did_ratio']:.3f} [{s['lo']:.3f},{s['hi']:.3f}]")
print("disagreements:", bad)
