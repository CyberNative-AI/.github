"""Amendment 02: re-fetch every eligible page image at the largest served thumbnail step.

Usage: python -I src/refetch.py FRAME_DIR LANG
The API's thumbnail step is capped at the file's nominal page width (500 or 960 px for many PDFs).
Request the same page at 1920 px, else 1280, else 960, else the API URL. Images go to img2/, and
the frame rows are rewritten in place (previous copy: frame.pre-a02.jsonl).
"""
import hashlib, json, re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from wsapi import api, fetch_bytes
from frame import dims

STEPS = (1920, 1280, 960)


def main():
    fdir, lang = Path(sys.argv[1]), sys.argv[2]
    d = fdir / lang
    src = d / "frame.jsonl"
    if not (d / "frame.pre-a02.jsonl").exists():
        shutil.copy(src, d / "frame.pre-a02.jsonl")
    rows = [json.loads(l) for l in (d / "frame.pre-a02.jsonl").read_text(encoding="utf-8").splitlines()]
    (d / "img2").mkdir(exist_ok=True)
    out = []
    for r in rows:
        if r["eligible"]:
            q = api(lang, action="query", prop="imageforpage", titles=r["title"], prppifpprop="thumbnail",
                    prppifpsize=1280)["query"]["pages"][0]
            url = q["imagesforpage"]["thumbnail"]
            url = "https:" + url if url.startswith("//") else url
            url = url.split("?")[0]
            img = step = None
            for w in STEPS:
                u = re.sub(r"(/(?:page\d+-|lossy-page\d+-)?)\d+px-", lambda m: f"{m.group(1)}{w}px-", url, count=1)
                try:
                    img, step, used = fetch_bytes(u), w, u
                    break
                except Exception:
                    continue
            if img is None:
                img, step, used = fetch_bytes(url), "api", url
            ext = "png" if img[:4] == b"\x89PNG" else "jpg"
            name = f"{r['idx']:03d}.{ext}"
            (d / "img2" / name).write_bytes(img)
            r.update(img=f"{lang}/img2/{name}", img_sha256=hashlib.sha256(img).hexdigest(), img_url=used,
                     img_step=step, img_px=dims(img))
        out.append(r)
    src.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    print(lang, "refetched", sum(r["eligible"] for r in out), flush=True)


if __name__ == "__main__":
    main()
