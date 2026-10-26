"""Remove link annotations whose URI points at the local test server; prove nothing else changed.
Usage: python -I strip_local_links.py IN_DIR OUT_DIR   -> OUT_DIR/*.pdf and prints a JSON report"""
import ctypes, hashlib, json, sys
from pathlib import Path
import pypdfium2 as pdfium
import pypdfium2.raw as c

LOCAL = (b"http://127.0.0.1", b"http://localhost", b"https://127.0.0.1", b"https://localhost")

def annots(doc, page):
    out = []
    for i in range(c.FPDFPage_GetAnnotCount(page.raw)):
        a = c.FPDFPage_GetAnnot(page.raw, i)
        sub = c.FPDFAnnot_GetSubtype(a)
        uri = None
        if sub == c.FPDF_ANNOT_LINK:
            act = c.FPDFLink_GetAction(c.FPDFAnnot_GetLink(a))
            if act and c.FPDFAction_GetType(act) == c.PDFACTION_URI:
                n = c.FPDFAction_GetURIPath(doc.raw, act, None, 0)
                buf = ctypes.create_string_buffer(n)
                c.FPDFAction_GetURIPath(doc.raw, act, buf, n)
                uri = buf.raw[:n].rstrip(b"\0")
        c.FPDFPage_CloseAnnot(a)
        out.append((i, sub, uri))
    return out

def fingerprint(path):
    doc = pdfium.PdfDocument(str(path))
    pages = []
    for page in doc:
        text = page.get_textpage().get_text_range()
        img = page.render(scale=2, grayscale=True)
        px = b"".join(bytes(img.buffer[y * img.stride:y * img.stride + img.width]) for y in range(img.height))
        pages.append({"text": hashlib.sha256(text.encode()).hexdigest(),
                      "render": hashlib.sha256(px).hexdigest(),
                      "annots": [(s, u.decode() if u else None) for _, s, u in annots(doc, page)]})
    return pages

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
report = {}
for p in sorted(src.glob("*.pdf")):
    doc = pdfium.PdfDocument(str(p))
    removed = 0
    for page in doc:
        for i, sub, uri in reversed(annots(doc, page)):
            if uri and uri.startswith(LOCAL):
                assert c.FPDFPage_RemoveAnnot(page.raw, i)
                removed += 1
    out = dst / p.name
    doc.save(str(out))
    doc.close()
    a, b = fingerprint(p), fingerprint(out)
    raw = out.read_bytes()
    report[p.name] = {
        "removed": removed,
        "pages": [len(a), len(b)],
        "text_same": [x["text"] for x in a] == [x["text"] for x in b],
        "render_same": [x["render"] for x in a] == [x["render"] for x in b],
        "annots_after": [x["annots"] for x in b],
        "local_bytes_after": sum(raw.count(s) for s in (b"127.0.0.1", b"localhost")),
        "sha256_in": hashlib.sha256(p.read_bytes()).hexdigest(),
        "sha256_out": hashlib.sha256(raw).hexdigest(),
    }
print(json.dumps(report, indent=1, sort_keys=True))
