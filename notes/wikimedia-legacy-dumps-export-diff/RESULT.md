# Result: the MediaWiki Content File Export is not yet a faithful replacement for the legacy XML dumps

Status: **frozen verdict CONTINUE** (summarise.py on the complete sample and history arms, 2026-10-15). The two targeted large wikis (enwiktionary, mgwiktionary) were still extracting when this was written. They cannot change the verdict, because the CONTINUE bar was met by the random sample. Their rows are appended below when complete.
Executed on our own hardware by the AI agent that designed the study. Not independently reproduced. Every number below is from `evidence/tallies.json`, `evidence/summary.json` and `evidence/compare/**`.

Update 2026-10-15, for publication (the two status lines above are kept as written): the two targeted large wikis are not part of this package. Their comparison and recent-changes files are left out, so every number here comes from the random sample, the history arm and the positive control, and `evidence/tallies.json` lists them under `targeted` as empty. The verdict rests on the random sample alone. A same-code rerun of 6 sampled wikis and the positive control finished after the status lines were written; its result is the last item under "Scope and limitations".

## Verdict inputs (frozen rules, PROTOCOL §6)

- Positive control (cywikisource, 12 planted defects): **12/12 correct, no extra differences** (`evidence/control.json`). This also shows that our text SHA-1 equals the API main-slot sha1.
- Current arm: 32 wikis drawn; **29 usable**. The 3 unusable wikis (crwiki, shnwikinews, hewikinews) are closed wikis with no 2026-10-01 export edition. **18 of 29** have at least one live-confirmed, adjudicated export-side defect (EXPORT_WRONG).
- History arm: 26 drawn; **23 usable** (the same 3 closed wikis); **12 of 23** have confirmed export-side defects.
- At least an estimated 100 export-side defects in a single wiki: fawikisource (est. 1,413), sourceswiki (est. 4,939), cywikisource (192), elwiktionary (133), plus history-arm cywikisource and fawikisource.
- Unusable count 3 ≤ 4, so the result is not INVALID.

## What is wrong (current arm, confirmed cases; post-hoc signatures from Amendment 01)

| Signature | Confirmed (checked) cases | Wikis | Mechanism evidence |
|---|---|---|---|
| S1: ProofreadPage page stored with length 0 but non-empty content | 590 checked (est. 6,544 incl. extrapolation) | cywikisource, fawikisource, sourceswiki | Legacy XML has `<text bytes="0" sha1=…>` with 87-89 bytes of content (the `<pagequality level="0">` "without text" marker). The export writes `<text bytes="0" />` with no content. The live main-slot sha1 matches the legacy content (raw-XML check of cywikisource page 6700). 0 of 45 checked cases have a move signal. |
| S2: wikitext revision exported with empty text | 81 | bclwikiquote 32, itwikiquote 20, elwiktionary 15, jawikibooks 6, ruewiki 6, fiwiktionary 2 | **59 of 59 checked are page-move null revisions** (a move log entry targets the title at the same second, or a move comment). Bikol Wikiquote's 32 come from one batch of moves on 2025-08-08. This is the known regression in Phabricator T417596 (reopened 2026-09-14 for enwiktionary 2026-09-01). It is still present in the 2026-10-01 edition on 6 of 29 random wikis. |
| S3: page missing from the export entirely | 156 (130 redirects, 26 non-redirects) | 9 wikis; elwiktionary 118 redirects, tnwiktionary 28 | Each missing page is live today with its latest revision equal to the legacy one, last edited between 2019 and 2025, and not in the W activity window. So T431872 (pages edited after the cutoff) does not explain them. The redirect share matches T417596's original "missing redirect events" diagnosis, which was marked fixed in April 2026. The 26 non-redirects include user pages, user .js pages and templates. |
| REV_DIFF: export has an older revision | 1 | svwikibooks | ns 6 (File) |

Other descriptive results (not part of the verdict):
- **Legacy-side defect:** mlwikiquote has 143 old (2007-2008) revisions whose legacy text does not match the live sha1, while the export's text does match. For these, the export is better. The history arm adds 200 METHOD_SUSPECT on the same wiki (log events in the adjudication window).
- BOTH_WRONG: history scwiki 3 and svwikibooks 2. METHOD_SUSPECT: current 2.
- Title style (META_DIFF, same page and revision, different title string): bowiki 4,316 of 22,816 pages, ruewiki 33, cawikiquote 8, shywiktionary 1. Spot checks show namespace prefixes rendered differently, for example a localized vs canonical "Template:" and a gendered user namespace. We have not matched this to a Phabricator task. An earlier draft of this result linked it to T410405; that task is about spaces versus underscores in titles and was resolved on 2026-03-02, so the link was wrong. These counts include every same-revision title difference whatever its timing class; 5 of them (bowiki 1, ruewiki 4) are on pages edited in the timing window. Joins on title between the export and other dumps will miss these pages.
- **Coverage (Amendment 01-A):** all 859 open wikis in the frame have both 2026-10-01 export editions. None of the 169 closed wikis has one: 134 have no export directory and 35 have an empty one. The sunset page does not mention closed wikis. After January 2027 their pages-meta-current/history XML stops with no replacement. [Update 2026-10-15: the sunset page's Timeline lists 20261201 (1 December 2026) as the last legacy edition in scope; none is published in January 2027.]

## Scope and limitations

- One edition (2026-10-01 export vs 20261001 legacy). Wikis are 300 MB or less in the random sample. The history arm covers small wikis only.
- The counts are confirmed cases from a capped live check (200 per wiki). Estimates extrapolate when the cap binds (fawikisource, sourceswiki).
- Root-cause labels are post hoc and based on 15 cases per wiki and type. They describe correlation with moves, redirects and content model, not the pipeline code.
- S1 loses only the ProofreadPage quality marker of blank scanned pages, not prose. Its practical impact is on proofreading-status statistics, not on article text. S2 and S3 lose real pages and texts.
- There is no legacy-vs-legacy noise comparator. Method error is bounded by the 12/12 positive control, the log adjudication and a raw-XML spot check.
- One AI agent ran everything. On 15 October 2026, about one hour after the main comparison (about 14 days after the 2026-10-01 editions), a second AI agent downloaded the dumps again and reran the same code on 6 of the sampled wikis and on the positive control: every count, every live check and the control output were identical to the evidence here. This shows the outputs are stable over that interval; it used the same code and is not an independent reproduction.

## Reproduce

Offline, from this folder, with Python 3.12 and the standard library only:

```
python3 src/summarise.py && python3 src/tally.py && sha256sum -c SHA256SUMS
```

`summarise.py` applies the frozen verdict rules to `evidence/compare/**` and rewrites `evidence/summary.json`. `tally.py` was added after the result to regenerate the counts quoted here; it rewrites `evidence/tallies.json`. Both rewritten files must still match `SHA256SUMS`.

Offline recompute is the supported operation for this bundle. It reads only files in this folder and writes only the two JSON files above.

Full rerun (historical; network). The collection scripts (`src/run_all.py`, `fetch.py`, `rcfetch.py`, `compare.py`, `control.py`, `coverage.py`, `signature.py`) are kept to document how the evidence was collected; they are not a supported release operation. Correction, 2026-10-15: an earlier copy of this section described the full rerun as bounded to 25 GB of downloads. The scripts do not enforce that bound or the 6-hour wall time: the download cap is checked only before each file, not during a transfer, and there is no job deadline (see the correction in `PROTOCOL.md` section 7). Anyone running them must apply their own disk, memory and wall-time limits outside the scripts. With those limits in place: set `DUMPS_WORK` to a scratch directory with enough space, then run `src/run_all.py rc|data|compare`, `src/control.py cywikisource` and `src/summarise.py` (frozen); `src/coverage.py` and `src/signature.py` (Amendment 01); the lean path for wikis with more than 3M revisions (Amendment 02). The extraction records a full rerun writes under `DUMPS_WORK` contain contributor user names, user IDs and IP addresses (`src/extract.py`); redact them before sharing. The legacy 20261001 files in scope return 404 from 2026-10-26 to 10-31 and from 11-15, and recent changes for W expire around 2026-10-28. A rerun must download before 10-26 or in the 11-01..11-14 window, and reuse `evidence/rc/*.json.gz`. In this public copy, user-namespace titles are removed from those files and from the comparison records (`EDITS.md`), so a rerun's timing control cannot match user pages by title.

## Data, contributors and edits

Data: page IDs, revision IDs, timestamps, SHA-1 hashes, sizes and public page titles from the Wikimedia XML dumps of
2026-10-01 and the public MediaWiki API, available from Wikimedia under CC BY-SA 4.0 and GFDL. No page text is stored.
Code (`src/`) is MIT-licensed (`LICENSE`).
