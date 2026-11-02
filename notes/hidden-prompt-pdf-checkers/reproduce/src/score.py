"""Scorer (host, stdlib + Pillow). Reads OUT/<stem>/run.json and renders, writes score.json + table.
usage: python3 -I score.py INDIR OUTDIR
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageChops

ANSI = re.compile(r"\x1b\[[0-9;]*m")
VIS_DIFF, VIS_MAX_PX = 40, 20
D1_HIDDEN = ("white", "invisible", "tiny", "off-page", "offpage", "off_page")


def toks(s: str) -> list[str]:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.findall(r"[a-z0-9]+", s)


def leaf_findings(obj):
    """Every dict that sits inside a list (a 'finding'), recursively."""
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += leaf_findings(v)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, dict):
                if not any(isinstance(x, list) and x and isinstance(x[0], dict) for x in v.values()):
                    out.append(v)
                out += leaf_findings(v)
    return out


def ftext(f: dict) -> str:
    return " ".join(str(v) for v in f.values() if isinstance(v, (str, int, float)))


def ftype(f: dict) -> str:
    for k in ("type", "kind", "category", "check", "name"):
        if k in f:
            return str(f[k]).lower()
    return ""


def hits(text: str, dist: list[str]) -> int:
    t = set(toks(text))
    return sum(1 for d in dist if d in t)


def vis_px(a: Path, b: Path) -> int | None:
    if not a.exists() or not b.exists():
        return None
    ia, ib = Image.open(a).convert("L"), Image.open(b).convert("L")
    if ia.size != ib.size:
        return -1
    d = ImageChops.difference(ia, ib).point(lambda v: 255 if v > VIS_DIFF else 0)
    return sum(1 for v in d.getdata() if v)


def marked_text(s: str) -> str:
    """Only the words PhantomLint marks as hidden: each char followed by U+0332 (word_spans.highlight_unicode)."""
    s = ANSI.sub("", s or "")
    return " ".join(w.replace("\u0332", "") for w in s.split() if "\u0332" in w)


def parse_json_out(out: str):
    """D1 prints a 'Scanning:' banner and progress bar before its JSON; parse from the first line starting with [ or {."""
    try:
        return json.loads(out)
    except Exception:
        lines = out.splitlines()
        for i, ln in enumerate(lines):
            if ln.lstrip().startswith(("[", "{")):
                return json.loads("\n".join(lines[i:]))
        raise


def has_tb(r: dict) -> bool:
    return "Traceback (most recent call last)" in (r.get("stderr") or "")


def main(indir: str, outdir: str) -> None:
    man = json.loads((Path(indir) / "manifest.json").read_text(encoding="utf-8"))
    od = Path(outdir)
    n1 = json.loads((od / "N1" / "run.json").read_text(encoding="utf-8"))
    base = set(toks(n1["extract"]["pdftotext"]["stdout"]))
    dist = {}
    for pid, p in man["payloads"].items():
        seen = []
        for t in toks(p):
            if len(t) >= 4 and t not in base and t not in seen:
                seen.append(t)
        dist[pid] = seen
    rows = []
    for f in man["files"]:
        stem = f["file"][:-4]
        r = json.loads((od / stem / "run.json").read_text(encoding="utf-8"))
        pid = f["payload"]
        dt = dist.get(pid, [])
        row = {"file": stem, "technique": f["technique"], "payload": pid}
        if pid:
            row["reach"] = {w: (hits(x["stdout"], dt) / len(dt) >= 0.5) for w, x in r["extract"].items()}
            row["reach_n"] = sum(row["reach"].values())
            row["reach_frac"] = {w: round(hits(x["stdout"], dt) / len(dt), 3) for w, x in r["extract"].items()}
        row["vis_px"] = {k: vis_px(od / stem / fn, od / "N1" / fn) for k, fn in (("mupdf", "mupdf.png"), ("poppler", "poppler.png"))}
        row["pixel_invisible"] = all(v is not None and 0 <= v <= VIS_MAX_PX for v in row["vis_px"].values())
        ocr_extra = set(toks(r["ocr300"]["stdout"])) - set(toks(n1["ocr300"]["stdout"]))
        row["ocr_legible_frac"] = round(sum(1 for d in dt if d in ocr_extra) / len(dt), 3) if dt else None
        row["hidden_to_human"] = row["pixel_invisible"] or (row["ocr_legible_frac"] is not None and row["ocr_legible_frac"] < 0.2)
        for arm in ("D1", "D2"):
            x = r[arm]
            try:
                js = parse_json_out(x["stdout"])
            except Exception:
                row[arm] = {"status": "error", "rc": x["rc"], "stderr_tail": (x["stderr"] or "")[-300:]}
                continue
            fs = leaf_findings(js)
            if arm == "D1":
                hid = [g for g in fs if any(k in ftype(g) for k in D1_HIDDEN)]
                pat = [g for g in fs if g not in hid]
            else:
                hid = [g for g in fs if "unicode" not in ftype(g) and "tag" not in ftype(g)]
                pat = []
            row[arm] = {
                "status": "ok", "rc": x["rc"], "n_findings": len(fs), "n_hidden": len(hid),
                "detect": any(hits(ftext(g), dt) >= 2 for g in hid) if pid else None,
                "pattern_hit": any(hits(ftext(g), dt) >= 2 for g in pat) if pid else None,
                "any_hidden_finding": bool(hid),
                "types": sorted({ftype(g) for g in fs}),
            }
        for arm in ("D3", "D4"):
            x = r[arm]
            hidtxt = marked_text(x.get("hidden_suspicious_phrases.txt"))
            if x["rc"] not in (0, 1) or has_tb(x):
                row[arm] = {"status": "error", "rc": x["rc"], "stderr_tail": (x["stderr"] or "")[-300:]}
                continue
            sus = marked_text(x.get("suspicious_phrases.txt"))
            row[arm] = {
                "status": "ok", "rc": x["rc"],
                "detect": (x["rc"] == 1 and hits(hidtxt, dt) >= 2) if pid else None,
                "gate_pass": (hits(sus, dt) >= 2) if pid else None,  # passed the phrase gate (before OCR test)
                "any_hidden_finding": x["rc"] == 1,
                "hidden_txt_chars": len(hidtxt),
            }
        rows.append(row)
    (od / "score.json").write_text(json.dumps({"distinctive": dist, "rows": rows}, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    # compact table
    def cell(r, a):
        v = r.get(a, {})
        if v.get("status") == "error":
            return "ERR"
        d = v.get("detect")
        return "-" if d is None else ("Y" if d else ".")
    lines = ["file        reach hidden  D1 D2 D3 D4  (D1pat D3gate | anyhidden D1 D2 D3 D4)"]
    for r in rows:
        lines.append(f"{r['file']:<11} {r.get('reach_n', '-')!s:>5} {str(r['hidden_to_human'])[0]:>6}  "
                     + "  ".join(cell(r, a) for a in ("D1", "D2", "D3", "D4"))
                     + f"   ({str(r.get('D1', {}).get('pattern_hit'))[0]} {str(r.get('D3', {}).get('gate_pass'))[0]} | "
                     + " ".join(str(r.get(a, {}).get('any_hidden_finding'))[0] for a in ("D1", "D2", "D3", "D4")) + ")")
    (od / "table.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
