"""Score the turn-suppressed rerun (written after the main run; stdlib only).

Usage: python -I src/noturn_score.py FRAME_DIR NOTURN_JSONL SCORE_PAGES_JSONL OUT_JSONL
NOTURN_JSONL is orientation.py --no-turn output. Writes one line per page, without text: key,
character error rate with the turn suppressed (same metric as score.py), the share of letters
in the expected script, and the main run's Indra and Tesseract-best error rates for comparison.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from score import cer_sg
from script_share import EXPECTED, scripts

fdir, runs, main_scores, out = (Path(a) for a in sys.argv[1:5])
main = {}
for line in main_scores.read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    main[r["key"]] = r
with open(out, "w", encoding="utf-8") as f:
    for line in runs.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        lang, idx = r["key"].split("/")
        extra = json.loads((fdir / lang / "pages" / f"{int(idx):03d}.extra.json").read_text(encoding="utf-8"))
        c = scripts(r["text"])
        n = sum(c.values())
        f.write(json.dumps({"key": r["key"], "rotation": r["rotation"],
                            "cer_I_noturn": round(cer_sg(r["text"], extra["gt_body"])[0], 5),
                            "expected_share_noturn": round(c[EXPECTED[lang]] / n, 4) if n else 0.0,
                            "cer_I_main": main[r["key"]]["cer_I"], "cer_TB_main": main[r["key"]]["cer_TB"]}) + "\n")
