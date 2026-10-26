# Docs themes cut off wide tables and long code lines when a page is printed or saved as PDF: 10 default themes measured in Chromium (October 26)

We built one test page with ten popular docs generators, each with its default theme, and
printed it to PDF with Chromium 151, the engine behind Chrome's Save as PDF. **All ten themes cut
off the right-hand end of a wide table. Five of the ten also cut off the end of a long code
line.** The same page as plain HTML with no CSS prints the whole table.

The cut-off text is not in the PDF at all: Chromium drops clipped glyphs, so searching or
copying the PDF misses it too.

In nine of the ten themes, two small print rules brought the whole table back in our test:
unclip the table, and let inline code inside table cells break. They did not fix the `mkdocs`
theme, which still printed 2 of 7 table values. **Unclipping alone was not enough.** Of
the nine themes the two rules fixed, unclipping alone fixed only Material, and it made the
table worse in VitePress and sphinx_rtd_theme (details below). The last column of the table below links the CSS we tested
for each theme.

## Why now

On October 26, "[Websites Should Be Printable](https://brennenputh.me/blog/printable-websites/)"
reached the Hacker News front page ([discussion](https://news.ycombinator.com/item?id=50241664)).
Its author found code blocks the hardest part to print. Their problem was code blocks not
breaking across pages. This note measures a different print problem on docs sites: content
wider than the page. We found no published side-by-side test of current default themes.

## Results

One page: a long `curl` command (about 240 characters on one line), a 7-column table with
inline code in every cell, and a long URL. Chromium 151 headless `page.pdf()`, US Letter,
0.4 inch margins, background graphics off. "Table values printed" counts the 7 cell values that
appear in full and visibly on the PDF page.

| Theme (version) | Long code line end | Table values printed, default | ... with unclip only | ... with unclip + cell code breaks | Print CSS we tested |
|---|---|---|---|---|---|
| Docusaurus 3.10.2 (classic) | kept | 3 of 7 | 5 | **7** | [docusaurus.AB.css](reproduce/fixes/docusaurus.AB.css) |
| Starlight 0.42.7 | kept | 3 of 7 | 5 | **7** | [starlight.AB.css](reproduce/fixes/starlight.AB.css) |
| VitePress 1.6.4 | **cut off** | 3 of 7 | 1 | **7** | [vitepress.AB.css](reproduce/fixes/vitepress.AB.css) |
| Material for MkDocs 9.8.0 | kept | 6 of 7 | **7** | **7** | [mkdocs-material.A.css](reproduce/fixes/mkdocs-material.A.css) |
| MkDocs 1.6.1 (`mkdocs` theme) | **cut off** | 1 of 7 | 1 | 2 | not fixed |
| mdBook 0.5.4 | kept | 3 of 7 | 3 | **7** | [mdbook.AB.css](reproduce/fixes/mdbook.AB.css) |
| Sphinx 9.2.0 + Alabaster 1.0.0 | **cut off** | 5 of 7 | 5 | **7** | [sphinx-alabaster.AB.css](reproduce/fixes/sphinx-alabaster.AB.css) |
| Sphinx + Furo 2025.12.19 | **cut off** | 4 of 7 | 5 | **7** | [sphinx-furo.AB.css](reproduce/fixes/sphinx-furo.AB.css) |
| Sphinx + sphinx_rtd_theme 3.1.0 | kept | 4 of 7 | 1 | **7** | [sphinx-rtd.AB.css](reproduce/fixes/sphinx-rtd.AB.css) |
| Sphinx + PyData 0.23.0 | **cut off** | 4 of 7 | 4 | **7** | [sphinx-pydata.AB.css](reproduce/fixes/sphinx-pydata.AB.css) |
| *Same page, plain HTML, no CSS* | cut off | 7 of 7 | | | |

The code-line ends come back with `white-space: pre-wrap` (in the same files). The `mkdocs`
theme also cut off the long URL and printed the whole page at two thirds of its size; no other
theme lost the URL. With the fixes, none of the marker words or table values that printed by
default was lost, and none of them overlapped other printed text. The nine restored themes
printed at full size except Material (86%), Alabaster (71%) and Furo (96%); the `mkdocs` page
printed at 67%.

## What causes it

- **Tables.** Most themes make tables scroll sideways on screen, either with
  `display: block; overflow: auto` on the table itself (Docusaurus, Starlight, VitePress) or
  with a scrolling wrapper around it (Material, mdBook, Furo, sphinx_rtd_theme, PyData). Paper
  has no scrollbar, so everything past the content width is clipped. Alabaster does not clip
  its table; it is simply wider than Chromium will shrink.
- **Why unclipping alone is not enough.** Without the clip, a table of unbreakable inline code
  is wider than the page. Chromium shrinks an over-wide page to fit, but only down to two
  thirds of its size; anything wider is still cut. Letting the cell code break
  (`overflow-wrap: anywhere`) lets the table fit the page width. Alabaster and PyData also
  need `white-space: normal` on `span.pre`, because Sphinx's `basic.css`, which both load, sets
  it to `nowrap`.
- **Code lines.** Five themes keep `white-space: pre` with a scrolling code block when
  printing. The other five already switch code to `pre-wrap` in their print CSS.
- **The plain page** keeps its table because without theme padding, fonts and clipping it is
  narrow enough for Chromium's shrink-to-fit.

## Also seen: tabs and collapsed blocks

Material for MkDocs is the only theme here that prints the hidden panels of a tab set and opens
collapsed `<details>` blocks. Every other tab or collapsible implementation we tested prints
only the visible tab and the collapsed summary. That may be intended. Chromium does not open
`<details>` for printing on its own.

## Method

- Each generator built the same content, written in its own source format by
  [`make_sites.py`](reproduce/src/make_sites.py), with its default theme and configuration.
  Docusaurus and Starlight came from their `create-*` starters (Starlight's pinned to its
  0.42.7 release, with the package lock from our run). Every block holds a marker
  word, and a reader checks every marker character on the PDF: in the text layer and with ink
  on the rendered page.
- Instrument checks ran on both passes of the first run, on a control page: text that should
  print (including text wrapped over six lines) read as printed, and text that is clipped,
  hidden or covered read as lost. That control page is not in this folder; the plain page the
  scripts print carries two of its checks (clipped and hidden text).
- We printed in a container with no network. Material therefore used fallback fonts, and the
  `mkdocs` theme ran without its highlight.js CDN stylesheet.
- We wrote down the method and decision rule before printing any theme. The default results
  came from that run. The unclip-only and unclip-plus-break columns came from a later run with
  the same pages and reader. Its default prints matched the first run in all 210 marker
  readings. Two passes of the later run gave identical readings.
- After correcting the published commands, we reran them from [`reproduce/`](reproduce/) on
  the same machine: same resolved versions, and readings identical to the later run's first
  pass for all 30 theme prints. The plain page printed all 7 table values.
- Six of our 30 predictions, written before printing, were wrong: we expected mdBook to cut
  its code line (it wraps), Alabaster, Furo and PyData to keep theirs (they cut it), MkDocs to
  keep the long URL (it cut it), and Alabaster to keep its table (it cut it).

## Limitations

- Chromium only. Firefox and Safari were not tested and may print differently.
- We printed with headless `page.pdf()`. It uses the same engine as the Save as PDF dialog,
  but the dialog adds headers and footers and has its own scale setting.
- One synthetic page, US Letter, default configuration only. A site's own CSS may already
  fix this.
- The 7-value table count and the fix runs came after the first results.
- Docs-to-PDF exporters that drive headless Chromium probably behave the same way. We did not
  run any.
- The MkDocs result is not explained; neither fix restored its table.
- We ran this on our own machine; nobody else has reproduced it.

## Files

[`reproduce/`](reproduce/) holds the page generator, the build and print scripts, the PDF
reader, the fix stylesheets and the raw readings of both passes of the later run. It also holds
20 of that run's PDFs: the default print and the unclip-plus-break print of each theme. In ten
of them we removed a link annotation that pointed at the local test server; text and page
images are unchanged. See [`reproduce/README.md`](reproduce/README.md) for the commands, the hash
lists and the license (MIT for our files).

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
