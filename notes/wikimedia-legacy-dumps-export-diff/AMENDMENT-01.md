# Amendment 01 (append-only, 2026-10-15): post-hoc descriptive checks

These checks were added after the freeze. None of them changes a frozen rule, an input, or the verdict computed by `summarise.py`. They are labelled post hoc wherever they are reported.

## A. Edition coverage (src/coverage.py → evidence/coverage-editions.jsonl)

Trigger: crwiki's export directory exists but is empty (the fetch got a SHA256SUMS 404). A HEAD request was sent to `.../{dataset}/{wiki}/2026-10-01/xml/bzip2/SHA256SUMS` for all 894 frame wikis that have an export directory, for both datasets.

## B. Root-cause signatures (src/signature.py → evidence/signatures.jsonl)

Trigger: the confirmed cases clustered. Examples: Bikol Wikiquote's 32 empty texts all fall in one hour of 2025-08-08, and the Wikisource cases are all `proofread-page`. Prior art read after the run started: Phabricator T417596 was reopened on 2026-09-14 for the regression "moved articles don't have any page text". T431872 covers pages edited after the snapshot cutoff being dropped. T410405 covers inconsistent title styles. [Correction added for publication, 2026-10-15: T410405 is about spaces versus underscores in titles and was resolved on 2026-03-02. It does not explain the namespace-prefix differences we found; see RESULT.md.] Current arm only. The first 15 EXPORT_WRONG cases (by key) per wiki and type were checked through the public API for:
- the revision comment,
- move log entries within ±2 s of the revision whose target is this title (a move writes a null revision on its target),
- all log events on the title,
- the page's current redirect flag.

A further check reads the legacy `bytes` attribute and the content model of every confirmed TEXT_DIFF from the extraction records, with no extra network calls. A raw-XML spot check of one case (cywikisource page 6700) read both decompressed files with grep, independently of extract.py.
