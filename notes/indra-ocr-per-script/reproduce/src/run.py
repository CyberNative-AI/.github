"""Runner (inside the image built from Dockerfile, --network none).

Usage: python run.py FRAME_JSONL IN_ROOT OUT_JSONL [WORKERS]
Arms per eligible page: I (Indra OCR 1.1.2, OCR mode, furniture kept, 1 thread),
TB (Tesseract + tessdata_best <lang>), TD (Tesseract + Debian tessdata <lang>),
TE (Tesseract + tessdata_best eng: the model card's comparator).
Replicates: every page whose idx % 10 == 0 runs I and TB a second time (rep=1).
Appends one JSON line per (page, arm, rep) as it finishes; skips keys already present.
"""
import json, os, subprocess, sys, time
from multiprocessing import Pool
from pathlib import Path

os.environ["OMP_THREAD_LIMIT"] = "1"
BEST = "/opt/tessdata_best"
TIMEOUT = 300
_conv = None


def indra(path):
    global _conv
    if _conv is None:
        import indra_ocr
        _conv = indra_ocr.load(path="/opt/indra-models", threads=1, mode="ocr", furniture=True)
    pages = list(_conv.convert(path))
    return "\n".join(p.text for _, p in pages), {"source": [p.source for _, p in pages]}


def tess(path, lang, tessdata):
    cmd = ["tesseract", path, "stdout", "-l", lang] + (["--tessdata-dir", tessdata] if tessdata else [])
    r = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT)
    if r.returncode != 0:
        raise RuntimeError(f"rc={r.returncode} {r.stderr.decode('utf-8', 'replace')[-300:]}")
    return r.stdout.decode("utf-8", "replace"), {}


def task(t):
    key, lang, tl, img, arm, rep = t
    t0 = time.monotonic()
    row = {"key": key, "lang": lang, "arm": arm, "rep": rep}
    try:
        if arm == "I":
            text, extra = indra(img)
        elif arm == "TB":
            text, extra = tess(img, tl, BEST)
        elif arm == "TD":
            text, extra = tess(img, tl, None)
        elif arm == "TE":
            text, extra = tess(img, "eng", BEST)
        row.update(ok=True, text=text, **extra)
    except Exception as e:
        row.update(ok=False, err=f"{type(e).__name__}: {e}"[:400])
    row["ms"] = round((time.monotonic() - t0) * 1000)
    return row


def main():
    frame, root, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    done = set()
    if out.exists():
        for l in out.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            done.add((r["key"], r["arm"], r["rep"]))
    tasks = []
    for l in frame.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        if not r.get("eligible"):
            continue
        key = f"{r['lang']}/{r['idx']:03d}"
        reps = [0, 1] if r["idx"] % 10 == 0 else [0]
        for arm in ("I", "TB", "TD", "TE"):
            for rep in (reps if arm in ("I", "TB") else [0]):
                if (key, arm, rep) not in done:
                    tasks.append((key, r["lang"], r["tess"], str(root / r["img"]), arm, rep))
    print(f"tasks {len(tasks)} (done {len(done)})", flush=True)
    with Pool(workers, maxtasksperchild=200) as pool, open(out, "a", encoding="utf-8") as f:
        for n, row in enumerate(pool.imap_unordered(task, tasks, chunksize=1), 1):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            if n % 100 == 0:
                print(f"{n}/{len(tasks)}", flush=True)
    print("RUN_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
