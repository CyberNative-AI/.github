# Reproduce: free hidden-text checkers on the Parauapebas court payload

Everything behind the note one directory up. All PDFs here are synthetic: the names and facts
in the petition are invented.

## Files

- `src/gen.py` writes the 44 PDFs and `manifest.json` (deterministic: no timestamps or IDs, so
  `python3 -I src/gen.py DIR` gives byte-identical files; the hashes are in `inputs/manifest.json`).
- `inputs/` the 44 PDFs. File names are `Tnn-PAYLOAD.pdf`: T00 visible, T01–T13 the hiding
  techniques listed in `gen.py` (`payload_ops`), PAYLOAD `PT` (the court's text), `EN` (the
  English rendering), `CTRL` (two of PhantomLint's own phrases). `N1`, `N2` are clean petitions;
  N2 has a white heading on a navy banner.
- `src/run.py` runs, for each PDF: four text extractors (pypdf, pdfminer.six, PyMuPDF,
  pdftotext), two renders (MuPDF, Poppler) and a 300 dpi Tesseract read for the visibility
  check, and the four checker configurations. It keeps every command, exit code, stdout and stderr.
- `src/score.py` applies the scoring rule and writes `out/score.json` and `out/table.txt`.
- `src/recount.py` is a second count that shares no code with `score.py` (its own word lists,
  JSON reading and a stricter three-word rule). Its output is `out/recount.txt`.
- `src/gate.py` computes how close each payload comes to PhantomLint's default phrase list,
  using PhantomLint's own windowing and model, from the text alone (`out/gate.json`).
- `out/raw-run-json.tgz` holds the raw `run.json` of every PDF.
- `image/` the container (OS tools, Tesseract English, Poppler) and the script that builds the
  four Python environments with pinned versions.

## Versions tested

| Tool | Version | Source |
|---|---|---|
| hidden-text-detector | commit `ce9e505dc1c128701e921e8d7e1a133c7ff28db8` (2026-07-28), PyMuPDF 1.26.3 | https://github.com/wppoland/hidden-text-detector (MIT) |
| pdf-injection-scanner | 0.2.1 | https://pypi.org/project/pdf-injection-scanner/ (MIT) |
| PhantomLint | commit `7f6200145abf9d1592118780e117d14541a18dae` (2025-10-23) | https://github.com/tobycmurray/phantom-lint (BSD-3-Clause) |

PhantomLint ran twice per file: with its defaults, and with `--analyze passthrough`.

## Rerun

`./run.sh WORKDIR` fetches the two GitHub tools at those commits, builds the image and the
environments (this step needs the network), runs all 44 PDFs with `--network none`, then scores
and recounts. It needs Docker, git and Python 3 with Pillow. The detection columns of
`table.txt` and the totals in `recount.txt` should match ours.

## Scoring rule

A checker flagged a file if it reported a hidden-text finding that quotes at least two
distinctive words of the payload (words of four letters or more that the clean petition does not
contain). pdf-injection-scanner's pattern-only findings ("Suspicious Pattern") do not count as
hidden-text findings. For PhantomLint, the words must be among those it marks as hidden
(underlined with U+0332) and its exit code must be 1. A version counts as hidden from a reader if
both renders at 100 dpi differ from the clean page by more than 40 grey levels in at most 20
pixels, or if Tesseract reads fewer than a fifth of the payload's distinctive words.

## License

Our files here (scripts, PDFs, outputs): MIT, CyberNative AI LLC. The tools we tested keep their
own licenses and are not included; `run.sh` downloads them.
