# Protocol: is the MediaWiki Content File Export a faithful replacement for the legacy XML dumps being sunset?

Status: FROZEN at the commit that adds this file. Amendments are append-only (`AMENDMENT-NN.md`).
Risk tier 1 (bounded public data downloads and public API reads; no accounts, no posting).

## 1. Why now (sources read 2026-10-14)

- Wikitech "Legacy content dumps sunset" (oldid 2468062, edited 2026-10-14): six legacy XML dumps (pages-meta-current, pages-meta-history, stub-meta-history, plus recombines) stop after January 2027. [Update added for publication, 2026-10-15: the Timeline section of the same page revision lists 20261201 (1 December 2026) as the last legacy edition in scope; no legacy dumps are published in January 2027.] The 20261001 files in scope return HTTP 404 from 2026-10-26 to 10-31, 11-15 to 11-30 and 12-06 to 12-31. Users are asked to migrate to the MediaWiki Content File Exports, which the page says "aim to be a faithful replacement" with only listed minor differences.
- Wikitech "MediaWiki Content File Exports" (oldid 2468169): the export "is compatible with MediaWiki's Special:Export, and with the legacy XML Dumps".
- Prior art: Phabricator T417596 (enwiktionary, February 2026): about 10,000 main-namespace pages were in the legacy dump but not in the export, and 2,282 export pages had empty text. It was listed as resolved on 2026-07-02. T431189 (July 2026) was a missing-file report and was resolved the next day. We found no outside equivalence check of a post-fix edition across many wikis.
- Design-time pilot on one tiny wiki excluded from the sample (punjabiwikimedia, 5 pages): the files are identical except for `<generator>` and an added `<parentid>0</parentid>`. A design-time listing check found that 134 of 1,028 wikis with a legacy 20261001 current dump have no export directory. All 134 are closed wikis in the sitematrix.

## 2. Question and hypotheses

Q: For the 2026-10-01 edition, do the exports contain the same pages, latest revisions (current arm) and revisions (history arm), with the same text, as the legacy 20261001 dumps they replace? Differences explained by activity in the snapshot window are excluded.

H0 (faithful): there are zero live-confirmed export-side defects in every arm.
H1 (not faithful): live-confirmed export-side defects appear in several wikis (frozen thresholds in section 6).

## 3. Frame and sample (src/frame.py, inputs hashed in the commit)

- Frame: wikis in `inputs/index.json.gz` (dumps.wikimedia.org/index.json fetched 2026-10-14) whose `metacurrentdump` is `done` with 20261001 files.
- Coverage arm C (descriptive): frame wikis absent from the `mediawiki_content_current/` listing (`inputs/export_dirs.txt`), split by sitematrix status (`inputs/sitematrix.json.gz`).
- Current arm sample: wikis present in both listings with legacy current size of 300 MB or less. Exclusions: the pilot wiki and the targeted wiki. Size bins (bytes, compressed legacy current): [0,1.15M), [1.15M,5M), [5M,25M), [25M,300M). Eight wikis per bin with `random.Random(13793)`, 32 wikis in total.
- Targeted arm T, current only, not part of the random-sample rate: enwiktionary (the T417596 site) and one scale-check wiki drawn with `random.Random(13794)` from the 55 wikis of 300 MB to 2.5 GB (drawn: mgwiktionary, 607 MB).
- History arm H: the 26 sampled wikis whose legacy `metahistorybz2dump` is `done`, 300 MB or less, and present in the history export listing (the list is in evidence/sample.json).

## 4. Procedure

1. `fetch.py WIKI ARM`: download every legacy file (verified against index.json sha1) and every export file listed in the export `SHA256SUMS` (verified by sha256). Downloads are sequential, one connection, with a URL-only User-Agent.
2. `extract.py WIKI ARM`: stream-parse every file into per-revision records. Only ids, titles, timestamps, contributor fields, the comment hash, model/format, the `bytes`/`sha1` attributes, the deleted flags, and the SHA-1 hex and UTF-8 length of the text are kept. No text is kept.
3. `rcfetch.py WIKI`: fetch all recent-changes rows (edit/new/log) in W = [2026-09-28T00:00Z, 2026-10-08T00:00Z] (timing control). This must run before about 2026-10-27, because recent changes keep about 30 days.
4. `run_all.py rc|data|compare` drives steps 1-4 resumably; `control.py cywikisource` runs the gate; `summarise.py` applies section 6.
5. `compare.py WIKI ARM`: key records by page id (current) or by (page id, revision id) (history). Classify each difference as MISSING_EXPORT, MISSING_LEGACY, REV_DIFF (current only), TEXT_DIFF (same revision, different text hash or text-deleted flag) or META_DIFF (secondary). `parentid` is not compared, because the pilot showed that the export adds `0` by design.
6. `summarise.py`: apply section 6.

## 5. Classification and live confirmation (in code: compare.py)

- TIMING: a differing revision's timestamp is at or after W start, or the page id, either title, or a move target appears in the W recent-changes rows.
- SNAPSHOT_LAG (otherwise): the present side's revision timestamp (for REV_DIFF, the newer revision) is later than the lacking side's wiki-wide maximum revision timestamp, so the lacking side's snapshot may predate it. It is reported and not counted as a defect.
- Otherwise the difference is UNEXPLAINED.
- The sunset page lists only non-content differences (no single-file bzip2 current file, no dumpstatus.json entry, no per-file RSS). None of these can produce a page or revision difference, so no DOCUMENTED class is needed. The added `parentid` is not compared.
- Live confirmation runs on UNEXPLAINED primary differences (MISSING_*, REV_DIFF, TEXT_DIFF), all of them or a seeded random 200 per wiki, through the public API.
  - current MISSING_EXPORT: the live latest revision equals the legacy revision, so EXPORT_WRONG (the page existed unchanged). MISSING_LEGACY is mirrored, giving LEGACY_WRONG.
  - current REV_DIFF: if the live latest revision timestamp is before W start, the side whose revision equals it is right and the other side is wrong.
  - history MISSING_EXPORT: the revision is live, visible, on the same page, and its live sha1 equals the legacy text hash, so EXPORT_WRONG. MISSING_LEGACY is mirrored.
  - TEXT_DIFF: the live main-slot sha1 of that revision (`rvslots=main`, `slotsha1`, hex SHA-1 of the main-slot text) decides: EXPORT_WRONG, LEGACY_WRONG, or BOTH_WRONG. BOTH_WRONG is reported separately and does not count as an export defect. If the sha1 is hidden, the result is UNCONFIRMED. History-arm checks also use the main-slot sha1.
  - Anything else is UNCONFIRMED (reported, not counted as a defect).
- Adjudication: each EXPORT_WRONG or LEGACY_WRONG case is checked for log events (any type) on either title from 2026-09-01 to W end. Any event turns it into METHOD_SUSPECT, which is not counted.
- Estimate: per arm-wiki, est = confirmed / checked × UNEXPLAINED primary count (it extrapolates when the cap of 200 applies).

## 5a. Positive control (control.py; gate)

On cywikisource (the first [25M,300M) sample wiki in sorted order), pages are drawn with `random.Random(13793)` from pages that meet all of these: identical in both files, latest revision before 2026-09-01, and not in W recent changes. The plants are made in in-memory copies: 5 pages removed from the export, 5 export text hashes altered, and 2 pages removed from the legacy side. The frozen classifier, live confirmation and adjudication must return exactly MISSING_EXPORT/EXPORT_WRONG ×5, TEXT_DIFF/EXPORT_WRONG ×5 and MISSING_LEGACY/LEGACY_WRONG ×2, with no other new difference. If it does not, the run is INVALID. The gate also checks that our text SHA-1 equals the API main-slot sha1.
- Also reported (descriptive): integrity counters per file set (sha1 attribute vs computed hash, bytes attribute vs length, missing text without a deleted flag, empty text with nonzero bytes), duplicate keys, and the maximum revision timestamp per side.

## 6. Frozen verdict rules (summarise.py)

- INVALID: the positive control fails, or more than 4 of the 32 sampled wikis are unusable. Unusable means no comparison (download or checksum failure after one retry), recent changes not covering W, or a revision timestamp at or after W end on either side (the window does not contain the snapshot). The history arm alone is invalid (excluded from the verdict and reported) if more than 4 of its 26 wikis are unusable.
- CONTINUE (report route): adjudicated live-confirmed export-side defects (EXPORT_WRONG) in at least 2 sampled wikis (current arm), OR an estimated 100 or more export-side defects in any single usable arm-wiki (sample, T or valid H), OR confirmed export-side defects in at least 2 history-arm wikis.
- CHANGE: any confirmed export-side defect below the CONTINUE bar.
- STOP: zero confirmed export-side defects in every usable arm. The result is a reproducible negative: "faithful on this edition and sample".
- Reported descriptively, not part of the verdict: legacy-side defects (LEGACY_WRONG, a reason to migrate sooner), BOTH_WRONG, METHOD_SUSPECT, SNAPSHOT_LAG, integrity counters, root-cause signatures (namespace × type of confirmed cases), and coverage arm C. For C, the 134 closed wikis without an export directory are a coverage fact that the sunset page does not mention. They are not a content defect, because the verdict concerns the exports that exist.

## 7. Resources, limits and abort clauses (enforced in code)

- Where it runs: host CPU, Python 3.12 stdlib only, no containers (no untrusted code is executed; dump files are parsed as data by expat). Disk: a local work directory. Cost: $0.
- Ceilings: at most 25 GB downloaded (fetch.py Abort); wall time at most 6 h; at most 4 parser processes; API at 1 request/s with maxlag=5.
- Abort: HTTP 429 from dumps or the API (Abort, stop the run); 5 consecutive failed file downloads (Abort); a checksum mismatch is retried once, then that wiki is marked unusable.
- Teardown: delete the raw `.bz2` files after the extraction records are written. Keep the derived records (ids, hashes, public titles, CC BY-SA metadata only) in the work directory until the decision. Check `du` afterwards.

[Correction added for publication, 2026-10-15: the heading above says these limits are enforced in code; only part of that is true. The 25 GB download cap is checked before each file starts, not while a file is transferred, so one large file can exceed it, and failed partial transfers are logged as 0 bytes. There is no 6-hour deadline in the code, so the scripts do not guarantee either limit. The collection scripts are kept as a historical record; any live collection needs disk, memory and wall-time limits applied outside the scripts. The offline recompute in RESULT.md is the supported operation.]

## 8. Limitations known before the run

One monthly edition only. Wikis are capped at 300 MB (except T), so the largest Wikipedias are untested. The history arm covers small wikis only, and there is no large-wiki history slice. There is no legacy-vs-legacy noise comparator: method error is bounded by the positive control and by adjudication only. Suppressed (oversight) actions are not in public recent changes, so they can leave UNEXPLAINED but UNCONFIRMED differences. That is why the verdict counts only live-confirmed defects. From November, the export applies a deliberate 7-10 day "safety buffer" that omits suppressed revisions, so later editions may differ by design. Executed on our host; not independently reproduced.

## 9. Pre-freeze forecast

A blind forecaster (one separate AI agent with no tools, given the draft protocol with sha256 87d5d3bf…edeb) gave P(CONTINUE)=0.40, P(CHANGE)=0.27, P(STOP)=0.18 and P(INVALID)=0.15. Its critique led to these changes: the SNAPSHOT_LAG class, main-slot sha1, BOTH_WRONG not counted, the positive control, log adjudication, extrapolated estimates, a scale-check wiki, the history-arm validity rule and a STOP that depends on export-side defects only. The full reply is in FORECAST.md.

## 10. Consumers

Research and data users of pages-meta-current/history who must migrate before January 2027 (the first 404 window starts 2026-10-26). If the CONTINUE verdict holds, whether to send a defect report to Wikimedia Data Engineering is decided separately. A short public note follows in either case.
