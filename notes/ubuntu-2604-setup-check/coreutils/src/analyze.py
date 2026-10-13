"""Frozen decision rule. usage: analyze.py  (reads results/, writes results/RESULT.json + results/divergent.jsonl)"""
import collections, json, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from compare import klass

ROOT = pathlib.Path(__file__).resolve().parent.parent
R = ROOT / "results"
DENOM = {"random-dedup": 1297, "top": 175}


def load(name):
    p = R / name
    return {r["id"]: r for r in map(json.loads, open(p))} if p.exists() else {}


def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    ph = k / n; d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d; h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 5), round(c + h, 5))


def is_mat(k):
    return k.startswith("material")


def main():
    cases = {r["id"]: r for r in map(json.loads, open(ROOT / "data" / "cases-all.jsonl"))}
    g1, g2, u1, u2, s1 = (load(f) for f in ("gnu94-1.jsonl", "gnu94-2.jsonl", "uutils-1.jsonl", "uutils-2.jsonl", "gnu97-1.jsonl"))
    conf = {(a, i): load(f"confirm-{a}-{i}.jsonl") for a in ("gnu94", "uutils", "gnu97") for i in (1, 2)}
    out = {"validity": {}}
    # validity
    ctl = [c for c in cases.values() if c["control"]]
    ctl_ok = [c["argv"] for c in ctl if is_mat(klass(g1.get(c["id"]), u1.get(c["id"]))) and is_mat(klass(s1.get(c["id"]), u1.get(c["id"])))]
    out["validity"]["controls_flagged"] = f"{len(ctl_ok)}/{len(ctl)}"
    det = {}
    for nm, a, b in (("gnu94", g1, g2), ("uutils", u1, u2)):
        ids = [i for i in cases if i in a and i in b]
        agree = sum(1 for i in ids if not is_mat(klass(a[i], b[i])))
        det[nm] = (agree, len(ids), len(cases))
    out["validity"]["determinism"] = {k: f"{v[0]}/{v[1]} (cases {v[2]})" for k, v in det.items()}
    complete = all(len(x) == len(cases) for x in (g1, g2, u1, u2, s1))
    # AMENDMENT-02: harness exec failures invalidate a pass (>0.5% EXEC_ERROR in any pass)
    exec_err = {nm: sum(1 for r in x.values() if r["rc"] == "EXEC_ERROR") for nm, x in (("gnu94-1", g1), ("gnu94-2", g2), ("uutils-1", u1), ("uutils-2", u2), ("gnu97-1", s1))}
    out["validity"]["exec_errors"] = exec_err
    complete = complete and all(v <= 0.005 * len(cases) for v in exec_err.values())
    valid = (len(ctl_ok) >= 5 and complete and all(v[0] >= 0.995 * v[2] for v in det.values()))
    out["validity"]["complete_passes"] = complete

    # per case classification + confirmation
    case_info = {}
    for cid, c in cases.items():
        k_gu, k_su, k_gs = klass(g1.get(cid), u1.get(cid)), klass(s1.get(cid), u1.get(cid)), klass(g1.get(cid), s1.get(cid))
        info = {"gu": k_gu, "su": k_su, "gs": k_gs}
        if is_mat(k_gu) or is_mat(k_su):
            stable = True
            for arm, first in (("gnu94", g1), ("uutils", u1), ("gnu97", s1)):
                for i in (1, 2):
                    r = conf[(arm, i)].get(cid)
                    if r is None or is_mat(klass(first.get(cid), r)):
                        stable = False
            info["confirmed"] = stable
        g = g1.get(cid) or {}
        info["exercised"] = g.get("rc") == 0 and (g.get("out_len", 0) > 0 or bool(g.get("fs_added")) or bool(g.get("fs_removed")))
        info["attributable"] = is_mat(k_gu) and is_mat(k_su) and info.get("confirmed", False)
        info["version_env"] = is_mat(k_gu) and not is_mat(k_su) and info.get("confirmed", False)
        case_info[cid] = info

    def cid_of(argv, piped, mode):
        import hashlib
        return hashlib.sha256(json.dumps([argv, piped, mode]).encode()).hexdigest()[:16]

    def consequential(occ, k):
        parts = k.split(":", 1)[1].split("+") if ":" in k else []
        return ("fs" in parts) or ("rc_flip" in parts and not occ["tolerated"]) or ("stdout" in parts and occ["consumed"])

    div_rows = []
    for stratum in ("random-dedup", "top"):
        occs = [json.loads(l) for l in open(ROOT / "data" / f"invocations-{stratum}.jsonl")]
        for mode in ("B", "A"):
            hit, hit_env, hit_cos = set(), set(), set()
            n_occ, n_ex = 0, 0
            per_cmd = collections.Counter()
            for o in occs:
                cid = cid_of(o["argv"], o["piped_in"], mode)
                inf = case_info[cid]
                n_occ += 1; n_ex += inf["exercised"]
                if inf["attributable"]:
                    if consequential(o, inf["gu"]) and consequential(o, inf["su"]):
                        hit.add(o["repo"]); per_cmd[o["argv"][0]] += 1
                        if mode == "B": div_rows.append({**o, "case": cid, "mode": mode, "stratum": stratum, "class_gu": inf["gu"], "class_su": inf["su"], "exercised": inf["exercised"]})
                    else:
                        hit_cos.add(o["repo"])
                elif inf["version_env"] and consequential(o, inf["gu"]):
                    hit_env.add(o["repo"])
            n = DENOM[stratum]
            out[f"{stratum}/{mode}"] = {"repos_hit": len(hit), "denominator": n, "R": round(len(hit) / n, 5), "wilson95": wilson(len(hit), n),
                                         "cosmetic_only_repos": len(hit_cos - hit), "version_env_repos": len(hit_env),
                                         "occurrences": n_occ, "exercised_share": round(n_ex / n_occ, 4), "per_command": dict(per_cmd.most_common())}
    p = out["random-dedup/B"]
    if not valid:
        ruling = "INVALID"
    elif p["R"] >= 0.010:
        ruling = "CONTINUE"
    elif p["R"] < 0.003:
        ruling = "STOP" if p["exercised_share"] >= 0.50 else "INCONCLUSIVE_LOW_SENSITIVITY"
    else:
        ruling = "CHANGE"
    out["ruling"] = ruling
    (R / "RESULT.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    (R / "divergent.jsonl").write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in div_rows))
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
