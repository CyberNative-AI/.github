# Scanned-page follow-up (November 2)

Scanning software that runs OCR stores the recognised text on top of the page image in invisible
render mode (`3 Tr`), so it can be searched and copied. hidden-text-detector `ce9e505` treats a page
where more than 80% of the text spans are in that mode as such a scan: it reports one INFO line,
"OCR text layer ... Most likely benign", and does not report the spans one by one
(`scripts/scan.py`, from line 491 at that commit). This test checks what that means for the
court's text.

## Files

- `gen.py` writes seven one-page PDFs from the clean petition `../inputs/N1.pdf`, rendered to a
  150 dpi greyscale image:
  - `S1` the image with an OCR layer: N1's ten text lines in invisible render mode, at their
    original positions.
  - `S2` S1 plus the court's text as three more invisible lines over a blank part of the image.
  - `S3` S1 plus the court's text as white ordinary text over a blank part of the image.
  - `S4`, `S5` as S2 and S1, but the image has Gaussian noise (sigma 4, fixed seed) and is stored as
    a JPEG at quality 75, closer to a real scan.
  - `T1` the image with an OCR layer written by Tesseract 5 (English model, `pdf` output; 111
    spans), not by us.
  - `T2` T1 plus the court's text as three invisible lines over a blank part of the image.
- `check.sh` runs inside the container from `../run.sh`: it writes the PDFs, then runs
  hidden-text-detector and pdf-injection-scanner on each, and checks whether pypdf extracts the
  court's text.
- `run.sh WORKDIR` runs `check.sh` offline. Run `../run.sh WORKDIR` first: it builds the image and
  the tool environments this reuses.
- `out/` our output: `run.txt` (exit codes and the pypdf check), each tool's JSON per file, and the
  SHA-256 of the PDFs we tested. The PDFs are not byte-identical between runs (PyMuPDF writes
  a new file ID each time), so compare the tool output, not the hashes.

## Result

| File | hidden-text-detector | pdf-injection-scanner | pypdf extracts the court's text |
|---|---|---|---|
| S1 scan, no payload | INFO only, exit 0 | nothing | no |
| S2 payload in the OCR layer | INFO only, exit 0 | nothing | yes |
| S3 payload as white text | 3 findings quote it, exit 1; also all 10 OCR lines | 3 findings quote it | yes |
| S4 noisy JPEG scan, payload in the OCR layer | INFO only, exit 0 | nothing | yes |
| S5 noisy JPEG scan, no payload | INFO only, exit 0 | nothing | no |
| T1 Tesseract OCR layer, no payload | INFO only, exit 0 | nothing | no |
| T2 Tesseract OCR layer, payload in it | INFO only, exit 0 | nothing | yes |

In S3 the three white lines bring the share of invisible spans down to 10 of 13 (77%), below the
80% switch, so hidden-text-detector also reports each of the ten legitimate OCR lines as hidden
text. Whether a page passes the 80% mark depends on how many spans it has: Tesseract's layer in T1
has 111.

## Limits

One synthetic page in each version. We have not tested real scanned filings, other OCR software,
or how often real scanned pages fall above or below the 80% mark.
