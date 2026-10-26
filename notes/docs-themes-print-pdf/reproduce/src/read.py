"""Classify each sentinel in each PDF as VISIBLE / CLIPPED / MISSING.

Usage: python3 -I read.py OUT_PASS_DIR   -> writes OUT_PASS_DIR/cells.json and prints a table

Rule (frozen):
- Each page's text layer is read per character (FPDFText_GetUnicode); whitespace, control chars and
  soft hyphens are dropped, so a sentinel wrapped across lines still matches (control ZQSPLITCTRL).
- MISSING = sentinel not fully in the text layer. Chromium culls clipped glyphs, so container
  clipping reads MISSING (controls ZQCLIPCTRL, ZQHALFCLIP).
- Otherwise, per occurrence, render the page at 2x grayscale and measure ink (pixels < 200) inside
  EVERY character box. VISIBLE if, for some occurrence, every character has ink >= INK_MIN; else
  CLIPPED (in the text layer but not on paper; control ZQCOVERCTRL: text under an opaque image, the fixed-header case).
- LOST = MISSING or CLIPPED. Each VISIBLE occurrence also records `overlap`: the number of other
  (non-sentinel, non-space) characters whose box intersects its character boxes.
"""
import json
import sys
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as raw

INK_MIN = 0.02
SCALE = 2
SENTINELS = ["ZQPARACTRL", "ZQCODECTRL", "ZQCODEEND", "ZQTABLECTRL", "ZQTABLEEND", "ZQURLEND",
             "ZQTAB1CTRL", "ZQTAB2", "ZQDETAILS", "ZQENDCTRL",
             "ZQCLIPCTRL", "ZQHIDDENCTRL", "ZQPOSCODE", "ZQOFFPAGE", "ZQHALFCLIP", "ZQSPLITCTRL",
             "ZQCOVERCTRL", "ZQBEYONDSHRINK", "ZQBEFOREPRINT", "ZQRULA", "ZQRULB"]


def ink(gray, w, h, box, ph):
    l, b, r, t = box
    x0, x1 = max(0, int(l * SCALE)), min(w, int(r * SCALE) + 1)
    y0, y1 = max(0, int((ph - t) * SCALE)), min(h, int((ph - b) * SCALE) + 1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    dark = sum(1 for y in range(y0, y1) for v in gray[y][x0:x1] if v < 200)
    return dark / ((x1 - x0) * (y1 - y0))


def inter(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def classify(pdf_path: Path):
    doc = pdfium.PdfDocument(str(pdf_path))
    found = {s: [] for s in SENTINELS}
    for pi in range(len(doc)):
        page = doc[pi]
        pw, ph = page.get_size()
        tp = page.get_textpage()
        n = tp.count_chars()
        chars, idx = [], []
        for i in range(n):
            c = chr(raw.FPDFText_GetUnicode(tp.raw, i))
            if c.isspace() or ord(c) < 32 or c in "\xad￾￿":
                continue
            chars.append(c); idx.append(i)
        flat = "".join(chars)
        bm = None
        for s in SENTINELS:
            start = flat.find(s)
            while start >= 0:
                ci = idx[start:start + len(s)]
                boxes = [tp.get_charbox(i) for i in ci]
                if bm is None:
                    img = page.render(scale=SCALE, grayscale=True)
                    W, H, stride, buf = img.width, img.height, img.stride, img.buffer
                    bm = ([bytes(buf[y * stride:y * stride + W]) for y in range(H)], W, H)
                gray, W, H = bm
                inks = [round(ink(gray, W, H, bx, ph), 3) for bx in boxes]
                own = set(ci)
                overlap = sum(1 for k, j in enumerate(idx) if j not in own and
                              any(inter(tp.get_charbox(j), bx) for bx in boxes)) if min(inks) >= INK_MIN else None
                found[s].append({"page": pi + 1, "chars": len(ci), "lines": len({round(bx[3] / 4) for bx in boxes}),
                                 "box": [round(min(b[0] for b in boxes), 1), round(min(b[1] for b in boxes), 1),
                                         round(max(b[2] for b in boxes), 1), round(max(b[3] for b in boxes), 1)],
                                 "min_ink": min(inks), "overlap": overlap})
                start = flat.find(s, start + 1)
    out = {}
    for s, occ in found.items():
        if not occ:
            out[s] = {"class": "MISSING", "occ": []}
        elif any(o["min_ink"] >= INK_MIN for o in occ):
            out[s] = {"class": "VISIBLE", "occ": occ}
        else:
            out[s] = {"class": "CLIPPED", "occ": occ}
    scale = None
    if found["ZQRULA"] and found["ZQRULB"]:
        scale = round((found["ZQRULB"][0]["box"][0] - found["ZQRULA"][0]["box"][0]) / 150.0, 3)
    return {"pages": len(doc), "scale": scale, "cells": out}


if __name__ == "__main__":
    d = Path(sys.argv[1])
    res = {p.name[:-4]: classify(p) for p in sorted(d.glob("*.pdf"))}
    (d / "cells.json").write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
    short = {"VISIBLE": "V", "CLIPPED": "C", "MISSING": "-"}
    print("arm.mode".ljust(28), "pg", "scale", " ".join(s[2:8].ljust(6) for s in SENTINELS))
    for k, v in res.items():
        print(k.ljust(28), str(v["pages"]).rjust(2), str(v["scale"]).ljust(5),
              " ".join(short[v["cells"][s]["class"]].ljust(6) for s in SENTINELS))
