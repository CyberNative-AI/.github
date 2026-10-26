# Docs themes print test: scripts and raw results

This folder is the record of our October 26 (UTC) runs. Run the steps below from this folder.
The first line makes a scratch directory, `work`, which each container mounts at `/work`.

## Steps

```sh
mkdir work && cp -r src fixes work/ && cd work
U="$(id -u):$(id -g)"

# 1. Write the test page in each generator's source format (Markdown/MDX, mdBook, MkDocs,
#    reStructuredText), plus g0 (the same page as plain HTML with no CSS) and g0-prewrap.
python3 src/make_sites.py fixtures

# 2. Build. Network on, for package installs only.
docker run --rm --user "$U" -v "$PWD":/work node:24.22.1 bash /work/src/build_node.sh
docker run --rm --user "$U" -v "$PWD":/work ghcr.io/astral-sh/uv:0.13.5-python3.12-trixie-slim \
  bash /work/src/build_py.sh

# 3. Print. No network.
docker run --rm --network none --ipc host --user "$U" -v "$PWD":/work -e HOME=/tmp \
  -e NODE_PATH=/work/pw/node_modules mcr.microsoft.com/playwright:v1.62.1-noble \
  node /work/src/print.mjs /work/sites /work/out/pass-a

# 4. Read. Writes cells.json, read.txt and cells7.json in out/pass-a.
docker run --rm --network none --user "$U" -v "$PWD":/work \
  ghcr.io/astral-sh/uv:0.13.5-python3.12-trixie-slim bash /work/src/read.sh pass-a
```

- `build_node.sh` builds Docusaurus 3.10.2 (`create-docusaurus` classic), Starlight, VitePress
  1.6.4 and mdBook 0.5.4 (release binary), and installs Playwright 1.62.1. Starlight's starter
  comes from its `@astrojs/starlight@0.42.7` release tag through `create-astro@5.3.1`, and is
  installed with `npm ci` from the `package.json` and `package-lock.json` in `src/starlight/`
  (Starlight 0.42.7, Astro 7.4.2).
- `build_py.sh` makes a Python 3.13 venv and installs MkDocs 1.6.1, mkdocs-material 9.8.0,
  Sphinx 9.2.0 with alabaster 1.0.0, furo 2025.12.19, sphinx-rtd-theme 3.1.0,
  pydata-sphinx-theme 0.23.0, sphinx-design 0.7.0, and pypdfium2 5.14.0 for the reader.
- Both build scripts write the resolved versions to `logs/*.versions`. Ours are in
  `out/*.versions`.
- `print.mjs` prints ten themes in three modes, plus `g0` as built:
  `docusaurus`, `starlight`, `vitepress`, `mkdocs-material`, `mkdocs`, `mdbook`,
  `sphinx-alabaster`, `sphinx-furo`, `sphinx-rtd`, `sphinx-pydata`.
  The modes are `default` (as built), `A` (`fixes/<theme>.A.css`: unclip only) and `AB`
  (`fixes/<theme>.AB.css`: unclip and let cell code break). Print settings: US Letter,
  0.4 inch margins, `printBackground: false`, viewport 1280x800, `networkidle` plus 1 s.
  Two markers 200 CSS px apart give the print scale. To print some arms only, pass them as a
  third argument, for example `.../out/pass-a docusaurus,g0-prewrap`.

Chromium in the Playwright image was 151.0.7922.34. The instrument control page from our first
run is not included; the `g0` page carries two of its checks (clipped and hidden text).

## How the reader decides

A marker counts as printed only if every one of its characters is in the PDF text layer (line
breaks and whitespace ignored, so wrapped text still matches) and every character box has ink
on the page rendered at 2x. Missing from the text layer = cut off (Chromium drops clipped
glyphs). In the text layer but without ink = covered. Overlapping characters are counted in
`cells7.json` (none in these runs).

## Files

- `src/`: page generator, build scripts, print script, reader (`read.py`, `posthoc_cells.py`,
  run by `read.sh`), and `strip_local_links.py` (below).
- `fixes/`: the print stylesheets, one pair per theme.
- `out/pass-a`, `out/pass-b`: two passes of the fix run (`read.txt`, `cells.json`,
  `cells7.json`, `meta.json`, `pdfs.sha256`). The readings match byte for byte; the PDF bytes
  differ only in their creation metadata. Each `pdfs.sha256` lists all 30 PDFs that pass
  printed, as printed. Those files are not all in this folder.
- `out/pdfs/`: 20 PDFs from pass A, the `default` and `AB` print of each theme (Material:
  its `A` print, linked in the note, read the same as `AB`). `SHA256SUMS` lists these 20 files.

The PDFs in `out/pdfs/` are not the printed bytes. `strip_local_links.py` re-saved all 20 and
removed the one link annotation in ten of them that pointed at the local test server
(`http://127.0.0.1:<port>/`). Page text and 2x page renders are identical before and after,
and the reader gives the same readings. `out/pdfs/strip-report.json` maps each original hash
(as listed in `out/pass-a/pdfs.sha256`) to the distributed file's hash.

The first run (default prints, a generic stylesheet we do not recommend, and the instrument
control pages) used the same generator, builds and reader. Its default readings match
`out/pass-a` in all 210 marker readings.

On October 26 (UTC), after correcting these commands, we reran steps 1 to 4 exactly as written
above. The resolved versions matched `out/*.versions`, and `cells.json` matched `out/pass-a` for
all 30 theme prints. In `g0`, all 7 table values printed, and the clipped and hidden checks
read as lost.

## License

Our scripts, stylesheets, readings and PDFs in this folder are offered under the MIT License
in [LICENSE](LICENSE), copyright 2026 CyberNative AI LLC. `src/starlight/package.json` and
`package-lock.json` are Starlight's basics starter manifest (MIT) as resolved by npm in our run.
