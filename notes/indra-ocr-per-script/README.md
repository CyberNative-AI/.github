# Indra OCR against Tesseract with the right language pack, per script: Indra is ahead on Thai, Arabic, Persian and Hebrew and level on most Indic scripts, but turns most upright Odia pages upside down (October 24)

[Indra OCR](https://github.com/datalab-to/indra) (PyPI `indra-ocr`, 1.1.2 released October 20)
reads 80+ languages on a CPU. Its README compares it with "Tesseract 5 (our run, Latin model)",
which its benchmark notes describe as Tesseract with the `eng` model, on every script. We ran both engines on 605
proofread page scans from 21 Wikisource language editions, giving Tesseract the language pack
for each page's language.

With the English model, Tesseract's character error rate was about 0.90 to 1.00 on every
non-Latin language: it barely reads them. With the right pack, Tesseract and Indra came out level on 10
of 18 non-Latin languages. Indra was more accurate on Thai, Arabic, Persian and Hebrew (and,
narrowly, Ukrainian). Tesseract was more accurate on Odia, but not because Indra reads Odia
badly: Indra's page-orientation step turned 18 of the 30 upright Odia pages upside down, and
the output came out in Sinhala, Armenian or Latin letters. With that turn suppressed, Indra and
Tesseract were level on Odia. Indra was about 2 to 7.5 times faster per page.

**If you OCR printed books in a non-Latin script on a CPU: on Thai, Arabic, Persian and Hebrew
scans, Indra 1.1.2 was clearly more accurate in our run. On most Indic scripts the two were
level, so speed can decide. For upright Odia scans, either use Tesseract with `ori`, or stop
Indra from turning pages (two lines of Python, below) and check that the output is in Odia.
Whatever you pick, check a few of your own pages: these are mostly older book scans, and the
right engine can differ for yours.**

## Results

Mean character error rate (CER) of the body text; lower is better. "Difference" is
Tesseract-best minus Indra, so a positive number means Indra had fewer errors; the 95%
interval comes from resampling books. "Prefill-like pages" are pages whose first Wikisource
revision already looked like Tesseract's output (see Limitations). The verdict is "Indra" or
"Tesseract" when the interval excludes zero and a second measure (character-pair F1) agrees,
otherwise "level".

| Language (wiki) | Pages | Indra | Tesseract, best pack | Tesseract, Debian pack | Tesseract, `eng` | Difference, best − Indra [95% CI] | Prefill-like pages | Median s/page, Indra / best | Verdict vs best | Verdict vs Debian |
|---|---|---|---|---|---|---|---|---|---|---|
| Thai (th) | 30 | 0.130 | 0.288 | 0.293 | 0.991 | +0.158 [+0.124, +0.194] | 0 | 0.5 / 2.7 | Indra | Indra |
| Arabic (ar) | 30 | 0.239 | 0.353 | 0.403 | 0.992 | +0.114 [+0.065, +0.163] | 1 | 0.3 / 2.1 | Indra | Indra |
| Persian (fa) | 30 | 0.212 | 0.304 | 0.319 | 0.995 | +0.091 [+0.041, +0.149] | 0 | 0.4 / 2.1 | Indra | Indra |
| Hebrew (he) | 25 | 0.225 | 0.292 | 0.301 | 0.985 | +0.068 [+0.027, +0.118] | 5 | 0.6 / 2.3 | Indra | Indra |
| Ukrainian (uk) | 30 | 0.086 | 0.100 | 0.098 | 0.966 | +0.014 [+0.002, +0.023] | 3 | 0.5 / 3.5 | Indra | level |
| Bengali (bn) | 30 | 0.163 | 0.150 | 0.126 | 0.971 | -0.013 [-0.032, +0.005] | 12 | 0.8 / 6.3 | level | Tesseract |
| Gujarati (gu) | 30 | 0.368 | 0.240 | 0.248 | 0.958 | -0.129 [-0.239, +0.007] | 8 | 0.8 / 2.3 | level | level |
| Hindi (hi) | 30 | 0.179 | 0.148 | 0.127 | 0.980 | -0.031 [-0.111, +0.037] | 10 | 0.9 / 3.3 | level | level |
| Armenian (hy) | 30 | 0.187 | 0.166 | 0.177 | 0.959 | -0.021 [-0.076, +0.035] | 12 | 1.1 / 2.0 | level | level |
| Kannada (kn) | 30 | 0.122 | 0.147 | 0.149 | 0.973 | +0.025 [-0.017, +0.082] | 10 | 0.8 / 2.2 | level | level |
| Malayalam (ml) | 30 | 0.249 | 0.253 | 0.240 | 0.980 | +0.004 [-0.082, +0.078] | 3 | 0.6 / 4.8 | level | level |
| Punjabi (pa) | 30 | 0.111 | 0.158 | 0.170 | 0.977 | +0.047 [-0.020, +0.122] | 9 | 0.5 / 2.5 | level | level |
| Russian (ru) | 30 | 0.196 | 0.219 | 0.225 | 0.950 | +0.023 [-0.004, +0.055] | 4 | 0.5 / 2.9 | level | Indra |
| Sanskrit (sa) | 30 | 0.212 | 0.239 | 0.239 | 0.977 | +0.027 [-0.024, +0.094] | 4 | 0.6 / 1.3 | level | level |
| Telugu (te) | 30 | 0.221 | 0.185 | 0.190 | 0.982 | -0.035 [-0.089, +0.002] | 4 | 0.7 / 2.5 | level | level |
| Odia (or) | 30 | 0.754 | 0.433 | 0.432 | 0.986 | -0.322 [-0.417, -0.219] | 5 | 0.5 / 2.2 | Tesseract | Tesseract |
| Greek (el) | 30 | 0.405 | 0.316 | 0.319 | 0.973 | -0.089 [-0.156, -0.025] | 5 | 0.8 / 2.4 | Tesseract, prefill-sensitive | Tesseract |
| Marathi (mr) | 30 | 0.172 | 0.096 | 0.097 | 0.967 | -0.076 [-0.122, -0.032] | 18 | 0.9 / 4.0 | Tesseract, prefill-sensitive | Tesseract |
| Tamil (ta) | 10 | 0.140 | 0.209 | 0.210 | 0.902 | – | 2 | 0.6 / 1.7 | too few pages | too few pages |
| English (en) | 30 | 0.038 | 0.048 | 0.050 | 0.048 | +0.010 [-0.000, +0.024] | 3 | 0.5 / 3.2 | level | Indra |
| French (fr) | 30 | 0.030 | 0.045 | 0.051 | 0.071 | +0.015 [-0.001, +0.038] | 12 | 0.6 / 2.5 | level | Indra |

"Prefill-sensitive": Tesseract's lead on Greek and Marathi did not hold once the prefill-like
pages were set aside (Marathi then had too few pages left to judge, Greek came out level). The
"vs Debian" column had no such check, and Bengali and Marathi have many prefill-like pages.

What the table says:

- **The README's Tesseract number is mostly the English model.** With `eng`, Tesseract's error
  rate is about 0.90 to 1.00 on every non-Latin language here. With the right pack it is 0.10
  to 0.43.
- **Indra is ahead on Thai and the right-to-left scripts.** Thai: 0.13 against 0.29, with fewer
  errors than Tesseract on all 30 pages. Arabic 0.24 against 0.35, Persian 0.21 against 0.30,
  Hebrew 0.22 against 0.29. Few of these pages were flagged as prefill-like, and the four
  verdicts hold with the flagged pages set aside. The flag is a heuristic, so this does not
  rule out prefill on pages it missed (see Limitations).
- **Most Indic scripts are level.** Bengali, Hindi, Kannada, Malayalam, Punjabi, Sanskrit and
  Telugu came out level against Tesseract's best pack. Gujarati leans toward Tesseract (0.24
  against 0.37) but its interval just reaches zero.
- **Debian's packs** (what `apt install tesseract-ocr-ben` installs) scored better than Indra
  on Bengali, Greek, Marathi and Odia, and were at least as good as the best packs on Bengali and
  Hindi.
- **Speed.** At one thread on 1920-pixel images, Indra's median was 0.3 to 1.1 seconds a page and
  Tesseract's 1.3 to 6.3, so Indra was about 2 to 7.5 times faster. The README's own speed
  figures come from other hardware and settings; ours agree only on the direction.

## Odia: upright pages turned upside down

On 18 of the 30 Odia pages, Indra's output is almost entirely in other scripts: at most 2% of
its letters are Odia, and most are Sinhala, Armenian or Latin. Every one of those 18 pages has
`"rotation": 180` in Indra's output. Its orientation model, `orient.onnx`, gave the
upside-down class a probability of 0.978 or more, above the 0.95 at which Indra turns the page.
The scans are upright, so Indra read upside-down Odia. 180° was the model's most likely class
on 27 of the 30 upright Odia pages; on 8 of the 12 pages it did not turn, the probability was
between 0.66 and 0.945, just under the threshold.

After the main run, we ran the 30 pages again with the turn suppressed (in Python, set
`indra_ocr.pipeline.ORIENT_MIN = 1.01` before `indra_ocr.load()`; the command-line tool has no
option for it):

| Odia pages | Pages | Indra, default | Indra, turn suppressed | Tesseract `ori` |
|---|---|---|---|---|
| Turned 180° | 18 | 0.99 | 0.45 | 0.46 |
| Not turned | 12 | 0.40 | 0.40 | 0.39 |
| All | 30 | 0.75 | 0.43 | 0.43 |

Mean character error rate. With the turn suppressed, 82% to 99.5% of the letters on the 18
pages are Odia, and Indra is level with Tesseract on Odia: the difference is +0.005, with a 95%
interval of -0.020 to +0.032, computed the same way as in the main table. Only suppress the turn if your scans
are upright: Indra then also stops turning pages that really are sideways or upside down.

One example is a clean, modern table of contents: page 4 of *Pratham Purush* (Jagannath
Prasad Das; [scan on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Pratham_Purush.pdf),
CC BY-SA 4.0). By default Indra returns no line in Odia; its lines come out in Latin,
Cyrillic, Armenian, Telugu, Bengali, Kannada and Myanmar letters. With the turn suppressed, it
reads the page in Odia.

Six of the 515 pages in the other 18 non-Latin languages were turned the same way: two Gujarati, two Malayalam,
one Hindi and one Telugu. Without the turn, their error rates fell from 0.85–1.00 to
0.01–0.27, so those four rows of the table above are somewhat worse for Indra than they would
be without this problem. No other non-Latin page was turned. We are reporting the Odia turns
to Indra's maintainers in the project's GitHub issues.

## What we ran

- **Pages.** For each of 21 Wikisource editions, validated pages (proofread by two people)
  drawn in a fixed random order, one page per book before any second page, until 30 pages
  passed the checks: at least 200 characters of body text, mostly in the expected script, and
  not a page made only of templates. Tamil reached only 10 of 600 candidates, because 590
  were licence-notice pages. The images are Wikimedia's 1920-pixel renders of each
  page. `reproduce/out/frame.jsonl` lists every candidate with its revision, image URL and image
  hash.
- **Engines.** `indra-ocr` 1.1.2 with its default models (Hugging Face tag v1.1.0), OCR mode,
  page headers and footers kept, one thread. Tesseract 5.5.0 (Debian 13) three ways: with the
  page language's `tessdata_best` model, with Debian's packaged model for the language, and with
  `tessdata_best` `eng`, the README's comparison. Default settings otherwise. The main run was
  one Docker container on an x86-64 desktop CPU, with no network.
- **Score.** Character error rate of the proofread body text against the best-matching stretch
  of the engine's output, with whitespace removed, so running heads and page numbers the
  proofreaders left out cost nothing. Indra and Tesseract-best ran a second time on 71 pages;
  all 142 repeats were byte-identical to the first run.
- **Order of work.** Before writing the method down, we ran all four engines on two pages (one
  Bengali, one Thai) to check the output format. We saw the first 120 characters of each output
  and the timings, but computed no error rates; both pages are also in the main run. We then
  wrote the question, page rules, scoring and verdict rules down, and amended them three times
  before the main run: twice to handle template-only pages correctly and once to fetch
  1920-pixel images instead of the 500- and 960-pixel ones the API returned for 358 pages. Everything in the Odia section (the
  script count of the output, the orientation probabilities and the run with the turn
  suppressed) was added after the main run; the results table is the main run as planned.
  Before the main run we expected Tesseract to win 4 to 8 languages, including Arabic and Persian;
  it won one robustly, and Indra won Arabic and Persian.

## Limitations

- Mostly older book scans (plus Thai Royal Gazette pages), not modern office documents, and
  30 pages or fewer per language, mostly one page per book. With 18 languages, one or two
  non-level verdicts could appear by chance, so a single narrow verdict, such as Ukrainian's, is
  weak evidence.
- Default settings for both engines. No PaddleOCR, Surya or EasyOCR comparison.
- The proofread text is the reference. Some pages started from a Tesseract draft, which favours
  Tesseract. We flag such pages ("prefill-like" above) with a heuristic that compares the first
  revision with Tesseract's output, and it can miss some. Indra's language models may have seen Wikisource
  text, which would favour Indra; we did not measure that.
- Tamil had too few pages. Chinese, Japanese, Korean, Khmer, Lao, Myanmar, Sinhala and Ethiopic
  were not tested.
- We ran this once on our own machine; nobody else has reproduced it.

## Files

[`reproduce/`](reproduce/) holds the page selection, runner, scorer, script-count and
orientation-check code, the Dockerfile, the page list with image hashes, the per-page and
per-language scores, and the per-page orientation probabilities. The page texts and the
engines' outputs are not included; they follow from the listed revisions and images. See [`reproduce/README.md`](reproduce/README.md).

Page scans and texts are from Wikisource and Wikimedia Commons, under CC BY-SA licences, with
authors and contributors listed on each page.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
