"""Scorer. usage: python score.py OUT_DIR [REPEAT_DIR] > score.json

Reads manifests and arm JSONL from OUT_DIR. Applies the frozen decision rule from PROTOCOL.md.
"""
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

import jiwer
from whisper.normalizers import BasicTextNormalizer, EnglishTextNormalizer

EN, BASIC = EnglishTextNormalizer(), BasicTextNormalizer()
VOCAL = {"laughing", "crying_baby", "coughing", "sneezing", "breathing", "snoring"}


def words(text, arm):
    if not text:
        return 0
    norm = BASIC if arm == "W_auto" else EN
    return len(norm(text).split())


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 5), round(c + h, 5)]


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def load(out, arm):
    p = out / f"{arm}.jsonl"
    if not p.exists():
        return None
    rows = {}
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        rows[r["id"]] = r
    return rows


def main():
    out = Path(sys.argv[1])
    rep = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    man = {s: [json.loads(l) for l in open(out / f"manifest-{s}.jsonl", encoding="utf-8")]
           for s in ("synth", "esc50", "speech")}
    arms = {a: load(out, a) for a in ("W_en", "W_auto", "T_tiny", "T_base", "M_tiny", "VAD")}
    res = {"arms": {}, "gates": {}, "synth": {}, "classes": {}}
    esc = man["esc50"]

    def seg(cid):  # VAD found speech; an errored VAD row counts as "segment found" (gate removes nothing)
        r = arms["VAD"][cid]
        return True if r["err"] else bool(json.loads(r["text"] or "[]"))

    def raw_false(arm, cid):  # errored clip counts as FALSE (conservative)
        r = arms[arm][cid]
        return True if r["err"] else words(r["text"], arm) > 0

    def false(arm, cid):
        if arm == "V":
            return seg(cid) and raw_false("T_tiny", cid)
        if arm == "W+V":
            return seg(cid) and raw_false("W_en", cid)
        return raw_false(arm, cid)

    complete = {a: (r is not None and all(c["id"] in r for c in esc) and all(c["id"] in r for c in man["speech"]))
                for a, r in arms.items()}
    res["complete"] = complete
    derived = {"V": complete["VAD"] and complete["T_tiny"], "W+V": complete["VAD"] and complete["W_en"]}
    fl = {}
    for arm in list(arms) + ["V", "W+V"]:
        if arm == "VAD" or not (complete.get(arm) or derived.get(arm)):
            continue
        f = {c["id"]: false(arm, c["id"]) for c in esc}
        fl[arm] = f
        k = sum(f.values())
        sens = [c for c in esc if c["category"] not in VOCAL]
        assert len(sens) == 1760, len(sens)
        ks = sum(f[c["id"]] for c in sens)
        res["arms"][arm] = {"false": k, "n": len(esc), "ftr": round(k / len(esc), 5), "ci95": wilson(k, len(esc)),
                            "sens_false": ks, "sens_n": len(sens), "sens_ftr": round(ks / len(sens), 5)}
        if arm in arms:
            secs = sorted(arms[arm][c["id"]]["sec"] for c in esc)
            res["arms"][arm]["median_sec_esc50"] = secs[len(secs) // 2]
            res["arms"][arm]["errors"] = sum(1 for r in arms[arm].values() if r["err"])
        by = defaultdict(lambda: [0, 0])
        for c in esc:
            by[c["category"]][0] += f[c["id"]]
            by[c["category"]][1] += 1
        res["classes"][arm] = {k2: v[0] for k2, v in sorted(by.items())}
        res["synth"][arm] = {c["id"]: (arms[arm][c["id"]]["text"] if arm in arms else None) for c in man["synth"]
                             if arm in arms and c["id"] in arms[arm]}

    # gates
    sp = man["speech"]
    for arm in ("W_en", "T_tiny", "T_base", "M_tiny", "W_auto"):
        if not complete.get(arm):
            continue
        hyp = [EN(arms[arm][c["id"]]["text"] or "") for c in sp]
        ref = [EN(c["ref"]) for c in sp]
        nonempty = sum(1 for h in hyp if h.strip())
        pairs = [(r, h) for r, h in zip(ref, hyp)]
        wer = jiwer.wer([r for r, _ in pairs], [h if h.strip() else "<empty>" for _, h in pairs])
        res["gates"][arm] = {"speech_nonempty": nonempty, "speech_n": len(sp), "wer": round(wer, 4)}
    if complete["VAD"]:
        nseg = sum(1 for c in sp if json.loads(arms["VAD"][c["id"]]["text"] or "[]"))
        res["gates"]["VAD"] = {"speech_with_segment": nseg, "speech_n": len(sp)}
    g = res["gates"]
    errs = {}
    for a in ("W_en", "T_tiny", "VAD"):
        if not complete.get(a):
            continue
        errs[a] = {st: sum(1 for c in man[st] if arms[a][c["id"]]["err"]) for st in ("esc50", "speech")}
    res["errors_by_set"] = errs
    gate_ok = (all(a in g and g[a]["speech_nonempty"] >= 0.98 * len(sp) and g[a]["wer"] <= 0.15 for a in ("W_en", "T_tiny"))
               and "VAD" in g and g["VAD"]["speech_with_segment"] >= 0.95 * len(sp)
               and all(a in errs and errs[a]["esc50"] <= 0.02 * len(esc) and errs[a]["speech"] <= 0.02 * len(sp)
                       for a in ("W_en", "T_tiny", "VAD")))
    # repeat gate
    rep_ok = None
    if rep is not None:
        rep_res = {}
        for arm in ("W_en", "T_tiny", "VAD"):
            r2 = load(rep, arm)
            if r2 is None:
                rep_res[arm] = None
                continue
            same = sum(1 for i, r in r2.items() if arms[arm] and i in arms[arm] and arms[arm][i]["text"] == r["text"])
            rep_res[arm] = {"identical": same, "n": len(r2)}
        res["repeat"] = rep_res
        rep_ok = all(v and v["n"] == 200 and v["identical"] >= 0.99 * v["n"] for v in rep_res.values())
    res["gates_ok"] = gate_ok
    res["repeat_ok"] = rep_ok

    verdict = "INCONCLUSIVE"
    if all(complete[a] for a in ("W_en", "T_tiny", "VAD")):
        w, v = fl["W_en"], fl["V"]
        n = len(esc)
        false_w = sum(w.values())
        removed = sum(1 for c in esc if w[c["id"]] and not seg(c["id"]))
        ub = wilson(false_w, n)[1]
        b = sum(1 for c in esc if w[c["id"]] and not v[c["id"]])
        c_ = sum(1 for c in esc if v[c["id"]] and not w[c["id"]])
        fw = false_w / n
        res["primary"] = {"false_W": false_w, "ftr_W": round(fw, 5), "ftr_W_ci95": wilson(false_w, n),
                          "removed_by_vad_R": removed, "ftr_WV": res["arms"]["W+V"]["ftr"],
                          "ref_ftr_V": res["arms"]["V"]["ftr"], "ref_W_only_vs_V": b, "ref_V_only_vs_W": c_,
                          "ref_mcnemar_p": mcnemar(b, c_)}
        # sensitivity: drop clips where W_en or VAD errored
        ok = [c for c in esc if not arms["W_en"][c["id"]]["err"] and not arms["VAD"][c["id"]]["err"]]
        res["primary"]["sens_drop_errors"] = {"n": len(ok), "false_W": sum(w[c["id"]] for c in ok)}
        if not gate_ok or rep_ok is False:
            verdict = "INVALID"
        elif ub <= 0.02:
            verdict = "SUPPORTED"
        elif fw >= 0.05 and removed >= 60 and removed >= 0.5 * false_w:
            verdict = "CHANGE"
        else:
            verdict = "DESCRIPTIVE"
        if rep is None and verdict != "INVALID":
            verdict += " (repeat gate pending)"
    res["literal_zeros_empty_W_en"] = ({k: arms["W_en"][k]["text"] == "" for k in ("zeros_1s", "zeros_5s", "zeros_30s")}
                                       if arms["W_en"] else None)

    # tool arm
    for t in ("TOOL_W_en", "TOOL_T_tiny"):
        tr = load(out, t)
        if tr is None:
            continue
        ctl = [r for r in tr.values() if r["set"] == "tool_ctl" and r["category"] == "positive"]
        ctl_ok = sum(1 for r in ctl if r["calls"]) >= 0.9 * len(ctl) if ctl else False
        esc_rows = [r for r in tr.values() if r["set"] == "esc50"]
        res.setdefault("tool", {})[t] = {
            "ctl_positive_with_call": sum(1 for r in ctl if r["calls"]), "ctl_positive_n": len(ctl), "ctl_ok": ctl_ok,
            "esc50_transcripts_sent": len(esc_rows),
            "esc50_with_call": sum(1 for r in esc_rows if r["calls"]),
            "esc50_with_call_conf_ge_0.4": sum(1 for r in esc_rows if r["calls"] and (r["confidence"] or 0) >= 0.4),
            "speech_baseline_sent": sum(1 for r in tr.values() if r["set"] == "speech"),
            "speech_baseline_with_call": sum(1 for r in tr.values() if r["set"] == "speech" and r["calls"]),
            "speech_baseline_with_call_conf_ge_0.4": sum(1 for r in tr.values() if r["set"] == "speech" and r["calls"]
                                                         and (r["confidence"] or 0) >= 0.4),
            "errors": sum(1 for r in tr.values() if r["err"])}
    res["verdict"] = verdict
    json.dump(res, sys.stdout, indent=1, sort_keys=True, ensure_ascii=False)
    print()


def repeat_ids():
    esc = sorted(json.loads(l)["id"] for l in open(sys.argv[2], encoding="utf-8"))
    return sorted(random.Random(13918).sample(esc, 200))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--repeat-ids":
        print("\n".join(repeat_ids()))
    else:
        main()
