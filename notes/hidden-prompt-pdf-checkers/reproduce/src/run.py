"""Runner (inside the hidpdf-os image, --network none, venvs mounted at /v, sources at /src).

For every input PDF: 4 extractors, 2 renderers (visibility check), 4 detector arms. Raw stdout/stderr/rc kept.
usage: python -I run.py INDIR OUTDIR [FILE ...]
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 300
EX = "/v/ex/bin/python"

EXTRACT_PY = r'''
import sys, json
path, which = sys.argv[1], sys.argv[2]
if which == "pypdf":
    from pypdf import PdfReader
    print("\n".join((p.extract_text() or "") for p in PdfReader(path).pages))
elif which == "pdfminer":
    from pdfminer.high_level import extract_text
    print(extract_text(path))
elif which == "pymupdf":
    import pymupdf
    print("\n".join(p.get_text() for p in pymupdf.open(path)))
'''

RENDER_PY = r'''
import sys, pymupdf
doc = pymupdf.open(sys.argv[1]); doc[0].get_pixmap(dpi=100, colorspace=pymupdf.csGRAY).save(sys.argv[2])
'''


def run(cmd, cwd=None, env=None):
    t = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT, cwd=cwd, env=env)
        return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout.decode("utf-8", "replace"),
                "stderr": p.stderr.decode("utf-8", "replace")[-20000:], "secs": round(time.time() - t, 2)}
    except subprocess.TimeoutExpired:
        return {"cmd": cmd, "rc": "timeout", "stdout": "", "stderr": "", "secs": TIMEOUT}


def main(indir, outdir, only):
    ind, od = Path(indir), Path(outdir)
    od.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, HF_HOME="/v/hf", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HOME="/tmp/h")
    Path("/tmp/h").mkdir(exist_ok=True)
    files = sorted(p for p in ind.glob("*.pdf") if not only or p.name in only)
    for pdf in files:
        stem = pdf.stem
        fo = od / stem
        fo.mkdir(exist_ok=True)
        rec = {"file": pdf.name}
        rec["extract"] = {w: run([EX, "-I", "-c", EXTRACT_PY, str(pdf), w]) for w in ("pypdf", "pdfminer", "pymupdf")}
        rec["extract"]["pdftotext"] = run(["pdftotext", "-layout", str(pdf), "-"])
        rec["render"] = {
            "mupdf": run([EX, "-I", "-c", RENDER_PY, str(pdf), str(fo / "mupdf.png")]),
            "poppler": run(["pdftoppm", "-r", "100", "-gray", "-png", "-singlefile", str(pdf), str(fo / "poppler")]),
        }
        rec["ocr300"] = run(["bash", "-c", 'pdftoppm -r 300 -gray -png -singlefile "$1" "$2/p300" && tesseract "$2/p300.png" - 2>/dev/null', "_", str(pdf), str(fo)])
        rec["D1"] = run(["/v/d1/bin/pdf-scan", str(pdf), "--json"], env=env)
        rec["D2"] = run(["/v/d2/bin/python", "-I", "/src/hidden-text-detector/scripts/scan.py", "--json", str(pdf)], env=env)
        for arm, extra in (("D3", []), ("D4", ["--analyze", "passthrough"])):
            o = fo / arm
            r = run(["/v/pl/bin/phantomlint", str(pdf), "--output", str(o)] + extra, cwd="/tmp", env=env)
            for fn in ("suspicious_phrases.txt", "hidden_suspicious_phrases.txt"):
                fp = o / fn
                r[fn] = fp.read_text(encoding="utf-8", errors="replace") if fp.exists() else None
            rec[arm] = r
        (fo / "run.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(stem, {k: rec[k]["rc"] for k in ("D1", "D2", "D3", "D4")}, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], set(sys.argv[3:]))
