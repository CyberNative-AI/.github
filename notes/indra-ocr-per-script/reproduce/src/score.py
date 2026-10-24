"""Scorer (stdlib only). Usage: python -I src/score.py FRAME_DIR RUNS_JSONL OUT_JSON

Primary: per-page CER = semi-global Levenshtein(gt_body, best OCR substring) / len(gt_body) on NFC
text with all whitespace and zero-width/soft-hyphen characters removed, capped at 1.0. Per wiki: mean paired
d = CER_TB - CER_I (positive = Indra better), 95% percentile CI from a book-cluster bootstrap
(10,000 resamples, seed 16397). Rulings and headline as written down before the run (see ../README.md).
"""
import json, random, re, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

SEED, B, MIN_N = 16397, 10000, 15
LATIN = {"en", "fr"}
ZW = dict.fromkeys(map(ord, "​‌‍⁠﻿­"), None)


def norm(t):
    t = unicodedata.normalize("NFC", t or "").translate(ZW)
    return re.sub(r"\s+", "", t)


def lev(a, b):
    """Global edit distance, Myers/Hyyro bit-parallel with Python ints."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    m = len(a)
    peq = {}
    for i, c in enumerate(a):
        peq[c] = peq.get(c, 0) | (1 << i)
    mask, hb = (1 << m) - 1, 1 << (m - 1)
    pv, mv, score = mask, 0, m
    for c in b:
        eq = peq.get(c, 0)
        xv = eq | mv
        xh = (((eq & pv) + pv) ^ pv) | eq
        ph = mv | (~(xh | pv) & mask)
        mh = pv & xh
        if ph & hb:
            score += 1
        elif mh & hb:
            score -= 1
        ph = ((ph << 1) | 1) & mask
        mh = (mh << 1) & mask
        pv = mh | (~(xv | ph) & mask)
        mv = ph & xv
    return score


def lev_sg(a, b):
    """Semi-global distance: all of a (ground truth) against the best substring of b (OCR).
    Leading and trailing OCR text costs nothing (running heads, page numbers, footers)."""
    if not a:
        return 0
    if not b:
        return len(a)
    m = len(a)
    peq = {}
    for i, c in enumerate(a):
        peq[c] = peq.get(c, 0) | (1 << i)
    mask, hb = (1 << m) - 1, 1 << (m - 1)
    pv, mv, score = mask, 0, m
    best = m
    for c in b:
        eq = peq.get(c, 0)
        xv = eq | mv
        xh = (((eq & pv) + pv) ^ pv) | eq
        ph = mv | (~(xh | pv) & mask)
        mh = pv & xh
        if ph & hb:
            score += 1
        elif mh & hb:
            score -= 1
        ph = (ph << 1) & mask
        mh = (mh << 1) & mask
        pv = mh | (~(xv | ph) & mask)
        mv = ph & xv
        if score < best:
            best = score
    return best


def cer_sg(ocr, gt):
    g = norm(gt)
    raw = lev_sg(g, norm(ocr)) / len(g)
    return min(1.0, raw), raw


def cer(ocr, gt):
    g = norm(gt)
    return min(1.0, lev(g, norm(ocr)) / len(g)), lev(g, norm(ocr)) / len(g)


def bigram_f1(ocr, gt):
    a, b = norm(ocr), norm(gt)
    ca, cb = Counter(a[i:i + 2] for i in range(len(a) - 1)), Counter(b[i:i + 2] for i in range(len(b) - 1))
    tp = sum((ca & cb).values())
    if not ca or not cb:
        return 0.0
    p, r = tp / sum(ca.values()), tp / sum(cb.values())
    return 0.0 if tp == 0 else 2 * p * r / (p + r)


def boot(pairs, rng):
    """pairs: list of (book, d). Book-cluster bootstrap of the mean."""
    by = defaultdict(list)
    for bk, d in pairs:
        by[bk].append(d)
    books = sorted(by)
    means = []
    for _ in range(B):
        s = n = 0
        for bk in (books[rng.randrange(len(books))] for _ in books):
            s += sum(by[bk]); n += len(by[bk])
        means.append(s / n)
    means.sort()
    return means[int(0.025 * B)], means[int(0.975 * B) - 1]


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


ARMS = ("I", "TB", "TD", "TE")


def page_rows(fdir, runs):
    frame = {}
    for fj in sorted(fdir.glob("*/frame.jsonl")):
        for l in fj.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            if r["eligible"]:
                k = f"{r['lang']}/{r['idx']:03d}"
                base = fdir / r["lang"] / "pages" / f"{r['idx']:03d}"
                r["gt"] = json.loads(Path(f"{base}.json").read_text(encoding="utf-8"))["gt"]
                r["extra"] = json.loads(Path(f"{base}.extra.json").read_text(encoding="utf-8"))  # required
                frame[k] = r
    res, reps = defaultdict(dict), {}
    for l in runs.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        (res[r["key"]].__setitem__(r["arm"], r) if r["rep"] == 0 else reps.__setitem__((r["key"], r["arm"]), r))
    pages, missing = [], []
    for k, fr in sorted(frame.items()):
        arms = res.get(k, {})
        if not all(a in arms and arms[a]["ok"] for a in ARMS):
            missing.append({"key": k, "arms": {a: (arms[a]["ok"] if a in arms else None) for a in ARMS},
                            "err": {a: arms[a].get("err") for a in arms if not arms[a]["ok"]}})
            continue
        body, first = fr["extra"]["gt_body"], fr["extra"]["first_body"] or ""
        row = {"key": k, "lang": fr["lang"], "book": fr["book"], "gt_body_len": len(norm(body)),
               "img_step": fr.get("img_step"), "img_w": (fr.get("img_px") or [None])[0],
               "gt_len": len(norm(fr["gt"])), "first_ts": fr["extra"]["first_ts"]}
        if len(norm(body)) < 100:
            missing.append({"key": k, "reason": "gt_body_under_100"})
            continue
        for a in ARMS:
            t = arms[a]["text"]
            row[f"cer_{a}"], row[f"cerraw_{a}"] = (round(x, 5) for x in cer_sg(t, body))
            row[f"cerfull_{a}"] = round(cer(t, fr["gt"])[0], 5)
            row[f"bf1_{a}"] = round(bigram_f1(t, body), 5)
            row[f"ms_{a}"] = arms[a]["ms"]
            row[f"first_{a}"] = round(cer_sg(t, first)[0], 5) if len(norm(first)) >= 100 else None
        # S1: the first revision looks like a Tesseract prefill of this page
        row["tb_prefill_like"] = bool(row["first_TB"] is not None and row["first_TB"] < 0.15
                                      and row["first_TB"] < row["first_I"])
        pages.append(row)
    return frame, res, reps, pages, missing


def rule(ps, comp, rng, metric="cer"):
    pairs = [(p["book"], p[f"{metric}_{comp}"] - p[f"{metric}_I"]) for p in ps]
    if len(ps) < MIN_N:
        return {"n": len(ps), "ruling": "UNDERCOVERED"}
    lo, hi = boot(pairs, rng)
    mean_d = sum(d for _, d in pairs) / len(pairs)
    bf = sum(p["bf1_I"] - p[f"bf1_{comp}"] for p in ps) / len(ps)  # positive = Indra better
    ruling = "INDRA_BETTER" if lo > 0 else ("TESS_BETTER" if hi < 0 else "TIE")
    if ruling == "INDRA_BETTER" and bf <= 0 or ruling == "TESS_BETTER" and bf >= 0:
        ruling = "METRIC_SPLIT"
    return {"n": len(ps), "mean_d": round(mean_d, 4), "ci95": [round(lo, 4), round(hi, 4)],
            "bf1_d": round(bf, 4), "indra_wins": sum(1 for _, d in pairs if d > 0),
            "tess_wins": sum(1 for _, d in pairs if d < 0), "ruling": ruling}


def main():
    fdir, runs, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    frame, res, reps, pages, missing = page_rows(fdir, runs)
    rep_check = {"n": 0, "identical": 0, "differ": []}
    for (k, a), r1 in sorted(reps.items()):
        r0 = res.get(k, {}).get(a)
        if not r0 or not r0["ok"] or not r1["ok"]:
            continue
        rep_check["n"] += 1
        if r0["text"] == r1["text"]:
            rep_check["identical"] += 1
        else:
            body = frame[k]["extra"]["gt_body"]
            rep_check["differ"].append({"key": k, "arm": a, "cer0": cer_sg(r0["text"], body)[0],
                                        "cer1": cer_sg(r1["text"], body)[0]})
    rng = random.Random(SEED)
    wikis = {}
    for lang in sorted({f["lang"] for f in frame.values()}):
        ps = [p for p in pages if p["lang"] == lang]
        w = {"n": len(ps), "n_books": len({p["book"] for p in ps}),
             "n_frame": sum(1 for f in frame.values() if f["lang"] == lang),
             "n_tb_prefill_like": sum(p["tb_prefill_like"] for p in ps)}
        for a in ARMS:
            for m in ("cer", "cerfull", "bf1"):
                w[f"mean_{m}_{a}"] = round(sum(p[f"{m}_{a}"] for p in ps) / len(ps), 4) if ps else None
            w[f"median_cer_{a}"] = median([p[f"cer_{a}"] for p in ps])
            w[f"median_ms_{a}"] = median([p[f"ms_{a}"] for p in ps])
        w["vs_TB"] = rule(ps, "TB", rng)
        w["vs_TD"] = rule(ps, "TD", rng)
        w["vs_TB_no_prefill"] = rule([p for p in ps if not p["tb_prefill_like"]], "TB", rng)
        r = w["vs_TB"]["ruling"]
        if r == "TESS_BETTER" and w["vs_TB_no_prefill"]["ruling"] != "TESS_BETTER":
            r = "TESS_BETTER_UNROBUST"
        w["ruling"] = r
        w["te_minus_tb_mean"] = round(w["mean_cer_TE"] - w["mean_cer_TB"], 4) if ps else None
        wikis[lang] = w
    ruled = {l: w["ruling"] for l, w in wikis.items() if l not in LATIN and w["ruling"] != "UNDERCOVERED"}
    nb = sum(v == "INDRA_BETTER" for v in ruled.values())
    nt = sum(v == "TESS_BETTER" for v in ruled.values())
    if not ruled:
        head = "UNDERCOVERED"
    elif nt >= 3 or nt >= len(ruled) / 3:
        head = "CARD_OVERSTATES"
    elif nb >= 2 * len(ruled) / 3 and nt == 0:
        head = "CARD_HOLDS_PER_SCRIPT"
    else:
        head = "MIXED"
    by_step = {}  # amendment 02 exploratory: d (TB - I) by served image step, non-Latin pages
    for st in sorted({str(p["img_step"]) for p in pages}):
        ps = [p for p in pages if str(p["img_step"]) == st and p["lang"] not in LATIN]
        if ps:
            by_step[st] = {"n": len(ps), "mean_d": round(sum(p["cer_TB"] - p["cer_I"] for p in ps) / len(ps), 4),
                           "mean_cer_I": round(sum(p["cer_I"] for p in ps) / len(ps), 4),
                           "mean_cer_TB": round(sum(p["cer_TB"] for p in ps) / len(ps), 4)}
    n_i_fail = sum(1 for m in missing if m.get("arms", {}).get("I") is False)
    summary = {"headline": head, "n_ruled_nonlatin": len(ruled), "indra_better": nb, "tess_better": nt,
               "other": len(ruled) - nb - nt, "rulings": ruled,
               "latin_controls": {l: wikis[l]["ruling"] for l in LATIN if l in wikis},
               "rulings_vs_TD": {l: w["vs_TD"]["ruling"] for l, w in wikis.items()},
               "n_pages_scored": len(pages), "n_frame": len(frame), "n_missing": len(missing),
               "i_fail_share": round(n_i_fail / len(frame), 4) if frame else None,
               "abort_i_fail": bool(frame) and n_i_fail / len(frame) > 0.10,
               "abort_tb_replicate": any(d["arm"] == "TB" for d in rep_check["differ"]),
               "replicates": rep_check, "by_img_step": by_step, "missing": missing, "wikis": wikis}
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    Path(str(out).replace(".json", "-pages.jsonl")).write_text(
        "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pages))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("wikis", "missing")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
