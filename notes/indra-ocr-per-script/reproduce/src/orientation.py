"""Orientation check (written after the main run). Runs inside the same image as run.py.

Usage: python orientation.py PAGE_LIST FRAME_DIR [--no-turn]
PAGE_LIST has one "key image-path" pair per line (image paths as in frame.jsonl, relative to
FRAME_DIR). For each page, prints one JSON line: key, Indra's page rotation, the orient.onnx
class probabilities (class k = k quarter turns, 4 = vertical) and, with --no-turn, the page
text read with the turn suppressed (ORIENT_MIN above 1, so orientation() never turns a page).
"""
import json, sys
import indra_ocr, indra_ocr.pipeline as pl

pages, root = sys.argv[1], sys.argv[2]
no_turn = "--no-turn" in sys.argv
if no_turn:
    pl.ORIENT_MIN = 1.01
probs = []
_orig = pl.OrtOCR.orientation_probs


def _logged(self, gray):
    p = _orig(self, gray)
    probs.append(None if p is None else [round(float(x), 3) for x in p])
    return p


pl.OrtOCR.orientation_probs = _logged
conv = indra_ocr.load(path="/opt/indra-models", threads=1, mode="ocr", furniture=True)
for line in open(pages, encoding="utf-8"):
    key, img = line.split()[:2]
    probs.clear()
    for _, page in conv.convert(f"{root}/{img}"):
        row = {"key": key, "rotation": page.rotation, "orient_probs": list(probs)}
        if no_turn:
            row["text"] = page.text
        print(json.dumps(row, ensure_ascii=False), flush=True)
