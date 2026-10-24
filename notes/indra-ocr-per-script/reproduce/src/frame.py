"""Build the frame: validated Wikisource pages, one per book first, seeded.

Usage: python -I src/frame.py OUTDIR [lang ...]
Writes OUTDIR/<lang>/cands.json, pages/<n>.json (wikitext, html, gt, html_body),
pages/<n>.extra.json (gt_body + first revision, eligible pages), img/<n>.<ext>, and appends
OUTDIR/<lang>/frame.jsonl (one row per candidate with eligibility verdict). Eligibility uses the
body-only text. Re-running reuses cached page renders and images of the same candidate index.
"""
import hashlib, html, json, random, re, struct, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from wsapi import api, fetch_bytes

SEED = 16397
TARGET = 30          # eligible pages per wiki
MAX_CANDS = 60       # non-template-only candidates examined per wiki, in seeded order
MAX_EXAMINED = 600   # amendment 01: absolute cap incl. template-only pages
MAX_MEMBERS = 2000   # most recent validated members pulled per wiki
WIKIS = {  # wiki: (tesseract lang, expected Unicode script word)
    "bn": ("ben", "BENGALI"), "ta": ("tam", "TAMIL"), "te": ("tel", "TELUGU"),
    "kn": ("kan", "KANNADA"), "ml": ("mal", "MALAYALAM"), "gu": ("guj", "GUJARATI"),
    "pa": ("pan", "GURMUKHI"), "or": ("ori", "ORIYA"), "hi": ("hin", "DEVANAGARI"),
    "mr": ("mar", "DEVANAGARI"), "sa": ("san", "DEVANAGARI"), "th": ("tha", "THAI"),
    "he": ("heb", "HEBREW"), "ar": ("ara", "ARABIC"), "fa": ("fas", "ARABIC"),
    "hy": ("hye", "ARMENIAN"), "el": ("ell", "GREEK"), "ru": ("rus", "CYRILLIC"),
    "uk": ("ukr", "CYRILLIC"), "en": ("eng", "LATIN"), "fr": ("fra", "LATIN"),
}


def script_of(ch):
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return None
    return name.split(" ")[0] if unicodedata.category(ch).startswith(("L", "M")) else None


def script_share(text, want):
    c = [script_of(ch) for ch in text]
    c = [x for x in c if x]
    return (sum(1 for x in c if x == want) / len(c)) if c else 0.0


DROP = re.compile(r"<style\b.*?</style>|<script\b.*?</script>|<div class=\"prp-page-qualityheader.*?</div>"
                  r"|<span class=\"mw-editsection.*?</span></span>", re.S)


def html_to_text(h):
    h = DROP.sub(" ", h)
    h = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</tr>|<hr[^>]*>", "\n", h)
    t = html.unescape(re.sub(r"<[^>]+>", "", h))
    t = unicodedata.normalize("NFC", t.replace(" ", " "))
    return "\n".join(l.strip() for l in t.splitlines() if l.strip())


def dims(b):
    """(width, height) from a PNG or JPEG header."""
    if b[:4] == b"\x89PNG":
        return list(struct.unpack(">II", b[16:24]))
    i = 2
    while i + 9 < len(b):
        if b[i] != 0xFF:
            i += 1
            continue
        if b[i + 1] in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return [w, h]
        i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return None


def template_only(body):
    """Amendment 01b: True if no text is written in the page itself, only template names
    (e.g. a licence-banner page). Template arguments count as page text."""
    t = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    t = re.sub(r"\{\{\s*[^|{}]*", "", t)      # template names
    t = re.sub(r"[{}|]|<[^>]+>", "", t)
    return len(re.sub(r"\s", "", t)) < 50


def members(lang):
    info = api(lang, action="query", meta="proofreadinfo", piprop="namespaces|qualitylevels")["query"]
    ns = info["proofreadnamespaces"]["page"]["id"]
    cat = [q["category"] for q in info["proofreadqualitylevels"] if q["id"] == 4][0]
    out, cont = [], {}
    while len(out) < MAX_MEMBERS:
        r = api(lang, action="query", list="categorymembers", cmtitle=f"Category:{cat}", cmnamespace=ns,
                cmsort="timestamp", cmdir="desc", cmlimit=500, cmprop="title|timestamp", **cont)
        out += r["query"]["categorymembers"]
        if "continue" not in r:
            break
        cont = {"cmcontinue": r["continue"]["cmcontinue"]}
    return ns, cat, out[:MAX_MEMBERS]


def book_of(title):
    t = title.split(":", 1)[1] if ":" in title else title
    return t.rsplit("/", 1)[0] if "/" in t else t


def order(mem):
    """Seeded order: shuffle books, one page per book; then second pages."""
    rng = random.Random(SEED)
    books = {}
    for m in mem:
        books.setdefault(book_of(m["title"]), []).append(m)
    keys = sorted(books)
    rng.shuffle(keys)
    for k in keys:
        books[k].sort(key=lambda m: m["title"])
        rng.shuffle(books[k])
    return [books[k][0] for k in keys] + [books[k][1] for k in keys if len(books[k]) > 1]


def main():
    outdir = Path(sys.argv[1])
    langs = sys.argv[2:] or list(WIKIS)
    for lang in langs:
        tl, want = WIKIS[lang]
        d = outdir / lang
        (d / "pages").mkdir(parents=True, exist_ok=True)
        (d / "img").mkdir(exist_ok=True)
        ns, cat, mem = members(lang)
        seq = order(mem)
        (d / "cands.json").write_text(json.dumps({"lang": lang, "ns": ns, "category": cat, "n_members": len(mem),
                                                  "n_books": len({book_of(m['title']) for m in mem}),
                                                  "seq": seq[:MAX_EXAMINED]}, ensure_ascii=False, indent=1))
        ok = counted = 0
        for i, m in enumerate(seq[:MAX_EXAMINED]):
            if ok >= TARGET or counted >= MAX_CANDS:
                break
            row = {"lang": lang, "idx": i, "title": m["title"], "book": book_of(m["title"]), "tess": tl}
            try:
                r = api(lang, action="query", prop="revisions|imageforpage|proofread", titles=m["title"],
                        rvprop="content|timestamp|ids", rvslots="main", prppifpprop="filename|size|thumbnail",
                        prppifpsize=2400)["query"]["pages"][0]
                rev = r["revisions"][0]
                wt = rev["slots"]["main"]["content"]
                row.update(revid=rev["revid"], rev_ts=rev["timestamp"], quality=r.get("proofread", {}).get("quality"))
                if template_only(re.sub(r"<noinclude>.*?</noinclude>", "", wt, flags=re.S)):
                    row.update(eligible=False, reasons=["template_only"])
                    with open(d / "frame.jsonl", "a", encoding="utf-8") as f:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    continue
                counted += 1
                ifp = r.get("imagesforpage") or {}
                cache = d / "pages" / f"{i:03d}.json"
                prev = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
                if prev.get("revid") == rev["revid"] or (prev.get("wikitext") == wt and prev.get("html")):
                    h = prev["html"]
                else:
                    h = api(lang, action="parse", oldid=rev["revid"], prop="text", disablelimitreport=1)["parse"]["text"]
                gt = html_to_text(h)
                body = re.sub(r"<noinclude>.*?</noinclude>", "", wt, flags=re.S)
                if prev.get("revid") == rev["revid"] and "html_body" in prev:
                    hb = prev["html_body"]
                else:
                    hb = api(lang, action="parse", text=body, title=m["title"], contentmodel="wikitext", prop="text",
                             disablelimitreport=1)["parse"]["text"]
                gt_body = html_to_text(hb)
                share = script_share(gt_body, want)
                reasons = []
                if row["quality"] != 4: reasons.append("not_q4")
                if len(re.sub(r"\s", "", gt_body)) < 200: reasons.append("short_gt")
                if share < 0.6: reasons.append(f"script_{share:.2f}")
                if re.search(r"<math|\{\||<table", body, re.I): reasons.append("math_or_table")
                if not ifp.get("thumbnail"): reasons.append("no_image")
                row.update(gt_chars=len(re.sub(r"\s", "", gt_body)), gt_full_chars=len(re.sub(r"\s", "", gt)),
                           script_share=round(share, 3), size=ifp.get("size"), filename=ifp.get("filename"))
                cache.write_text(json.dumps({"revid": rev["revid"], "wikitext": wt, "html": h, "gt": gt,
                                             "html_body": hb}, ensure_ascii=False))
                if not reasons:
                    url = ifp["thumbnail"]
                    url = "https:" + url if url.startswith("//") else url
                    old = [p for p in (d / "img").glob(f"{i:03d}.*")]
                    big = re.sub(r"/1280px-", "/1920px-", re.sub(r"/page(\d+)-1280px-", r"/page\1-1920px-", url))
                    if old:  # downloaded by the v1 pass of this same candidate (same seed and order)
                        img = old[0].read_bytes()
                        url = None  # v1 did not record which step it got; img_px records the size
                    else:
                        # Wikimedia serves fixed thumbnail steps; ask for 1920 px, else the API's 1280 px.
                        try:
                            img = fetch_bytes(big) if big != url else fetch_bytes(url)
                            url = big
                        except Exception:
                            img = fetch_bytes(url)
                    ext = "png" if img[:4] == b"\x89PNG" else "jpg"
                    name = f"{i:03d}.{ext}"
                    (d / "img" / name).write_bytes(img)
                    row.update(img=f"{lang}/img/{name}", img_sha256=hashlib.sha256(img).hexdigest(), img_url=url,
                               img_px=dims(img))
                    ok += 1
                    fr = api(lang, action="query", prop="revisions", titles=m["title"], rvdir="newer", rvlimit=1,
                             rvprop="ids|timestamp|user|comment|tags|content", rvslots="main")["query"]["pages"][0]["revisions"][0]
                    fwt = fr["slots"]["main"].get("content", "")
                    (d / "pages" / f"{i:03d}.extra.json").write_text(json.dumps({
                        "gt_body": gt_body, "first_revid": fr["revid"], "first_ts": fr["timestamp"],
                        "first_user": fr.get("user"), "first_comment": fr.get("comment"), "first_tags": fr.get("tags"),
                        "first_body": re.sub(r"<noinclude>.*?</noinclude>", "", fwt, flags=re.S)}, ensure_ascii=False))
                row["eligible"] = not reasons
                row["reasons"] = reasons
            except Exception as e:
                row.update(eligible=False, reasons=[f"error:{type(e).__name__}:{e}"[:200]])
            with open(d / "frame.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(lang, "members", len(mem), "eligible", ok, flush=True)


if __name__ == "__main__":
    main()
