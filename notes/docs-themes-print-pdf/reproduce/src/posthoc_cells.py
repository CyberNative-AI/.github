"""POST-HOC (after results): are the non-sentinel table cell values printed? Same per-character
reader and ink rule as read.py (content-stream order, whitespace dropped, ink in every char box).
Usage (container with pypdfium2): python -I posthoc_cells.py PASS_DIR > PASS_DIR/cells7.json
(A first attempt with host pdftotext was discarded: it reorders wrapped table cells by layout.)"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import read
read.SENTINELS = ["ZQTABLECTRL", "integer_or_null", "max_connection_pool_size", "ACME_MAX_CONNECTION_POOL_SIZE",
                  "v2026.10.0_preview", "worker_and_scheduler_processes", "ZQTABLEEND", "ZQRULA", "ZQRULB"]
out = {}
for p in sorted(Path(sys.argv[1]).glob("*.pdf")):
    if p.name.startswith(("ctrl", "g0-prewrap")):
        continue
    c = read.classify(p)["cells"]
    out[p.stem] = {s: (c[s]["class"], max([o["overlap"] or 0 for o in c[s]["occ"]] or [0])) for s in read.SENTINELS[:7]}
print(json.dumps(out, indent=1))
