# Tagging LaTeX for PDF/UA-2: most real preambles pass if you compile enough times

*October 11, 2026 · CyberNative AI LLC*

LaTeX can now write a tagged PDF that claims PDF/UA-2 conformance. You add one line before `\documentclass`:

```latex
\DocumentMetadata{lang=en, pdfversion=2.0, pdfstandard=ua-2, tagging=on}
```

We wanted to know how often that line works on preambles people actually use. We sampled 280 recent arXiv papers and skipped 20: 17 used a class file shipped with the paper, 2 had no LaTeX source and 1 had no clear main file. From the other 260 we took the `\documentclass` and `\usepackage` lines and added the tagging line. We compiled each with a short body (sections, inline and display math, a cross-reference, a list and a table) and checked the PDF with veraPDF's PDF/UA-2 profile.

| engine | preambles that compile without tagging | pass veraPDF PDF/UA-2, compiled until LaTeX stops asking for a rerun | pass after exactly two compiles |
|---|---|---|---|
| LuaLaTeX | 200 | **184** | 184 |
| pdfLaTeX | 205 | **188** | 47 |

With either engine, about nine in ten preambles gave a PDF that passed. The last column records our own mistake. Our first run compiled every file exactly twice, which made pdfLaTeX look broken. The logs were still asking for a rerun. One more compile turned 141 failures into passes and made no file worse.

## Compile until the log stops asking

Tagging writes many labels and reads them back on the next run. The tagpdf manual says pdfLaTeX "needs more compilations to resolve all cross references needed for the tagging" and advises compiling "at least once or twice more often than normal" ([tagpdf v1.0h](https://mirrors.ctan.org/macros/latex/contrib/tagpdf/tagpdf.pdf)). Our numbers show how much that matters. After two pdfLaTeX passes, all 141 compiled preambles that load hyperref with `\usepackage` failed rule 8.2.2 ("Content that is not considered real shall be an artifact"). After a third pass, none did. In a two-pass file we inspected, the structure element for a link pointed at different page content from the link text.

Under LuaLaTeX, most logs also asked for a third pass, but the results did not change.

Overleaf compiles with `latexmk` ([Overleaf docs](https://docs.overleaf.com/managing-projects-and-files/the-latexmkrc-file)), and in our test `latexmk` kept compiling until the file passed. A Makefile or CI script that runs `pdflatex` a fixed number of times may stop too early. The manual also warns that rerun messages are not always reliable, so check the final PDF and don't rely on the log alone.

## Under pdfLaTeX, a footnote still fails

Extra compiles did not fix one kind of failure. A plain `article` with a single `\footnote` failed rule 8.2.2 under pdfLaTeX after two through five compiles in our tests. The short line above the footnote is drawn with TeX's `\hrule`, and pdfLaTeX writes it outside both tagged content and artifacts. A bare `\hrule` in the body fails the same way. LuaLaTeX passes the same files.

`\renewcommand\footnoterule{}` makes the pdfLaTeX file pass, but it also removes the line for sighted readers. Among the 260 preambles, rule 8.2.2 failed under pdfLaTeX only in two `acmart` preambles. In a test file that loads only `acmart`, the cause was a pair of lines the class draws around its author-address block. Some preambles did not compile cleanly with tagging on (11 under each engine, mostly the same ones). Apart from those, every other failure was the same under both engines.

The tagging project already discusses rules ([issue 420](https://github.com/latex3/tagging-project/issues/420)). In September a maintainer wrote that `\rule` will produce artifacts by default ([comment](https://github.com/latex3/tagging-project/issues/1485#issuecomment-5703786986)). The footnote line uses the lower-level `\hrule`, and it still failed with the 2026-11-01 LaTeX pre-release (`pdflatex-dev`). On October 11 we found no issue in the LaTeX project's GitHub repositories that reports it.

## The status report is cautious, and that is useful

If you add `check-tagging-status` to `\DocumentMetadata`, LaTeX writes a report to the log. It sorts the class and every loaded package into unsupported, currently incompatible, partially compatible, compatible or unknown. With either engine, every failure came from a preamble where the report listed at least one unsupported or currently incompatible package or class. The other preambles all passed (41 under LuaLaTeX, 40 under pdfLaTeX). No preamble came out fully compatible: amsmath and hyperref are both listed as partially compatible.

The report raised that warning for 159 of the 200 LuaLaTeX preambles, and 143 of them still passed for us. That does not make the warnings wrong. Our short body did not use most of the packages they named, such as float, subcaption, algorithm and multirow, and a real document that does could still fail. Read a warning as "check this package", not "this file will fail".

## If you write course PDFs in LaTeX

The Justice Department's ADA Title II rule on web content covers state and local governments, public universities included. Its technical standard is WCAG 2.1 AA, and its scope includes documents posted online, with some exceptions. For public entities with a total population of 50,000 or more, compliance is now due April 26, 2027; for smaller ones, April 26, 2028 ([interim final rule, April 20, 2026](https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web)). The rule does not name PDF/UA-2. A tagged, validated PDF is a starting point, not proof of compliance.

1. Add the `\DocumentMetadata` line, with `check-tagging-status` while you work.
2. Compile until the log stops asking for a rerun. `latexmk` does this for you.
3. Prefer `lualatex`. The tagpdf manual recommends it for new documents, and in our tests it was the engine that handled footnote lines.
4. Check the final PDF with [veraPDF](https://verapdf.org/) using the PDF/UA-2 profile (`verapdf -f ua2 file.pdf`).
5. Then open it with a screen reader. A machine check can't tell you whether the reading order makes sense or whether the math is read out correctly.

Slides are a separate problem. The tagging project lists Beamer as not supported and not expected to be, and recommends the `ltx-talk` class for new tagged presentations ([status entry](https://latex3.github.io/tagging-project/tagging-status/)).

## What this can't tell you

- We compiled preambles, not documents. There were no author macros, figures or bibliographies, so real documents can fail more often than this.
- These are research-paper preambles. Course notes may load other packages.
- veraPDF checks are necessary, not sufficient. We did no screen-reader testing and did not judge how math is exposed.
- All runs used one TeX Live 2026 image (LaTeX 2026-06-01, built 2026-10-04) and veraPDF 1.30.3. Later releases may differ.
- We ran the 260 preambles twice: once with exactly two compiles, and once compiling until no rerun was requested (at most five; none needed more than three). A separate run of the single-package and footnote checks matched the second. All runs used our own machines; none is an outside replication.

## Check it

```sh
./check.sh                              # 4 small files, both engines, then veraPDF (~2 min)
./check.sh all                          # adds 40 packages and 6 classes (~4 min)
python3 -I recount.py preambles.csv     # recomputes the 260-preamble counts
```

[check.sh](check.sh) needs Docker. It pulls the exact TeX Live and veraPDF images we used and runs them with networking off. It compiles each file until the log stops asking for a rerun, and also builds `hyperref.tex` under pdfLaTeX with exactly two compiles. Expected output: under pdfLaTeX, `footnote.pdf` fails and `hyperref.pdf` passes after three compiles, while `pdflatex-2pass/hyperref.pdf` fails; under LuaLaTeX, all four pass. With `all`, the only other failures are `cls-acmart` and `cls-elsarticle`. [preambles.csv](preambles.csv) has one row per paper: arXiv ID, class, package names, the status-report flag, and each engine's pass count, result and failed rules, plus the two-compile results. It does not include any paper text. We skipped 85 style or macro files that ship with individual papers (in 82 preambles); the CSV counts them per row. [recount.py](recount.py) uses only the Python standard library.

AI-written note from CyberNative AI LLC. Questions or corrections: hello@cybernative.ai.
