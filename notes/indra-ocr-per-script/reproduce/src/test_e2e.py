"""Planted-outcome test of score.py rulings. Run: python -I src/test_e2e.py"""
import json, random, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
rng = random.Random(7)
ALPHA = "অআইঈউকখগঘচছজঝটঠডঢণতথদধনপফবভমযরলশসহ"


def txt(n):
    return "".join(rng.choice(ALPHA) for _ in range(n))


def corrupt(t, rate):
    return "".join(rng.choice(ALPHA) if rng.random() < rate else c for c in t)


def build(root):
    runs = []
    # bn: Tesseract clearly better; ta: Indra clearly better; te: 10 pages only (undercovered);
    # ml: Tesseract better only on pages whose first revision is Tesseract's output (prefill)
    plan = {"bn": (20, 0.02, 0.20, False), "ta": (20, 0.20, 0.02, False), "te": (10, 0.02, 0.2, False),
            "ml": (20, None, None, True), "en": (20, 0.05, 0.05, False)}
    for lang, (n, tb_rate, i_rate, prefill) in plan.items():
        d = root / lang / "pages"
        d.mkdir(parents=True)
        rows = []
        for i in range(n):
            gt = txt(400)
            if prefill:
                is_pf = i < 14
                tb = corrupt(gt, 0.01 if is_pf else 0.05)
                ind = corrupt(gt, 0.12 if is_pf else 0.05)
                first = tb if is_pf else ""
            else:
                tb, ind, first = corrupt(gt, tb_rate), corrupt(gt, i_rate), ""
                if lang == "en":  # identical outputs: the ruling must be TIE
                    ind = tb
            rows.append({"lang": lang, "idx": i, "title": f"P:{lang}{i}", "book": f"B{i}", "tess": "x",
                         "eligible": True, "reasons": [], "img": "x"})
            (d / f"{i:03d}.json").write_text(json.dumps({"wikitext": "", "html": "", "gt": "HEAD" + gt}))
            (d / f"{i:03d}.extra.json").write_text(json.dumps({"gt_body": gt, "first_ts": "2020", "first_body": first}))
            key = f"{lang}/{i:03d}"
            for arm, t in (("I", "12" + ind), ("TB", tb + "99"), ("TD", tb), ("TE", txt(50))):
                runs.append({"key": key, "lang": lang, "arm": arm, "rep": 0, "ok": True, "text": t, "ms": 10})
            if i == 0:
                runs.append({"key": key, "lang": lang, "arm": "TB", "rep": 1, "ok": True, "text": tb + "99", "ms": 10})
        (root / lang / "frame.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    # one failed Indra arm in ta: page leaves every comparison
    for r in runs:
        if r["key"] == "ta/019" and r["arm"] == "I":
            r.update(ok=False, text=None, err="RuntimeError: planted")
    (root / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))


with tempfile.TemporaryDirectory() as t:
    root = Path(t)
    build(root)
    subprocess.run([sys.executable, "-I", str(HERE / "score.py"), str(root), str(root / "runs.jsonl"),
                    str(root / "s.json")], check=True, capture_output=True)
    s = json.loads((root / "s.json").read_text())
    w = s["wikis"]
    assert w["bn"]["ruling"] == "TESS_BETTER", w["bn"]
    assert w["ta"]["ruling"] == "INDRA_BETTER" and w["ta"]["n"] == 19, w["ta"]
    assert w["te"]["ruling"] == "UNDERCOVERED", w["te"]
    assert w["ml"]["vs_TB"]["ruling"] == "TESS_BETTER" and w["ml"]["ruling"] == "TESS_BETTER_UNROBUST", w["ml"]
    assert w["ml"]["n_tb_prefill_like"] == 14, w["ml"]
    assert s["latin_controls"]["en"] == "TIE", s["latin_controls"]
    assert s["rulings"] == {"bn": "TESS_BETTER", "ml": "TESS_BETTER_UNROBUST", "ta": "INDRA_BETTER"}, s["rulings"]
    assert s["headline"] == "CARD_OVERSTATES", s["headline"]  # 1 of 3 ruled = 1/3
    assert s["replicates"]["n"] == 5 and s["replicates"]["identical"] == 5 and not s["abort_tb_replicate"]
    assert s["n_missing"] == 1 and not s["abort_i_fail"]
    assert w["bn"]["mean_cer_TE"] > 0.9
    print("E2E OK", s["headline"], s["rulings"])
