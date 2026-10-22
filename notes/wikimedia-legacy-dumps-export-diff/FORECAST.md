# Pre-freeze blind forecast

Draft protocol sha256 at forecast time: 87d5d3bf63e89d4e2e67c46bef1521e38ab74a0bc1b039a996b535fcf8fcedeb
Forecaster: one separate AI agent with no tools and no prior context, 0 tool uses, about 51 s, 2026-10-14. Exact prompt and full final reply below, except that the study ID is removed from the quoted draft's title.

## Prompt

```text
You are a blind forecaster for a research protocol. Do not use any tools: no web, no files, no shell. Answer only from the protocol text below and your general knowledge. Do not include any email address or company name in your answer.

Task:
1. Give your probabilities that the frozen verdict will be CONTINUE, CHANGE, STOP and INVALID (they must sum to 1), with a 2-4 sentence rationale.
2. List the 3-6 most serious design flaws you see, each one with a concrete fix: wrong controls, classification rules that can misfire, a missing comparator, bugs in the logic as described, and threats to the validity of the "export wrong" confirmation. Be specific and skeptical.

PROTOCOL (draft, verbatim):
-----
# [study ID removed] protocol: is the MediaWiki Content File Export a faithful replacement for the legacy XML dumps being sunset?

## 1. Why now (sources read 2026-10-14)
- Wikitech "Legacy content dumps sunset" (edited 2026-10-14): six legacy XML dumps (pages-meta-current, pages-meta-history, stub-meta-history, plus recombines) stop after January 2027. The 20261001 files in scope return HTTP 404 from 2026-10-26 to 10-31, 11-15 to 11-30 and 12-06 to 12-31. Users are asked to migrate to the MediaWiki Content File Exports, which the page says "aim to be a faithful replacement" with only listed minor differences.
- Wikitech "MediaWiki Content File Exports": the export "is compatible with MediaWiki's Special:Export, and with the legacy XML Dumps".
- Prior art: Phabricator T417596 (enwiktionary, February 2026): about 10,000 main-namespace pages were in the legacy dump but not in the export, and 2,282 export pages had empty text. It was listed as resolved on 2026-07-02. T431189 (July 2026) was a missing-file report and was resolved the next day. We found no outside equivalence check of a post-fix edition across many wikis.
- Design-time pilot on one tiny wiki excluded from the sample (5 pages): the files are identical except for <generator> and an added <parentid>0</parentid>. A design-time listing check found that 134 of 1,028 wikis with a legacy 20261001 current dump have no export directory. All 134 are closed wikis.

## 2. Question and hypotheses
Q: For the 2026-10-01 edition, do the exports contain the same pages, latest revisions (current arm) and revisions (history arm), with the same text, as the legacy 20261001 dumps they replace? Differences explained by activity in the snapshot window are excluded.
H0 (faithful): there are zero live-confirmed export-side defects in every arm. H1: live-confirmed export-side defects appear in several wikis.

## 3. Frame and sample
- Frame: wikis whose legacy metacurrentdump is done with 20261001 files (1,028).
- Coverage arm C (descriptive): frame wikis absent from the export listing, by sitematrix status.
- Current arm sample: wikis present in both with legacy current compressed size <= 300 MB, excluding the pilot and targeted wiki. Size bins [0,1.15M), [1.15M,5M), [5M,25M), [25M,300M) bytes; 8 per bin seeded random, 32 wikis.
- Targeted arm T: enwiktionary current (~2 GB compressed each side), the T417596 site.
- History arm H: sampled wikis whose legacy pages-meta-history is done, <= 300 MB, and present in the history export listing.

## 4. Procedure
1. Download every legacy file (verified against published sha1) and every export file in the export SHA256SUMS (sha256).
2. Stream-parse into per-revision records: ids, titles, timestamps, contributor fields, comment hash, model/format, bytes/sha1 attributes, deleted flags, SHA-1 hex and UTF-8 length of text.
3. Fetch all recent-changes rows (edit/new/log) via the public API in W = [2026-09-28T00:00Z, 2026-10-08T00:00Z] (timing control).
4. Key records by page id (current) or (page id, revision id) (history). Classify each difference: MISSING_EXPORT, MISSING_LEGACY, REV_DIFF (current only), TEXT_DIFF (same revision, different text hash or text-deleted flag) or META_DIFF (secondary). parentid not compared.

## 5. Classification and live confirmation
- TIMING: a differing revision's timestamp >= W start, or the page id, either title or a move target appears in W recent-changes rows. Otherwise UNEXPLAINED.
- Live confirmation on UNEXPLAINED primary differences (all, or seeded random 200 per wiki), public API:
  - current MISSING_EXPORT: live latest revision equals the legacy revision -> EXPORT_WRONG. MISSING_LEGACY mirrored -> LEGACY_WRONG.
  - current REV_DIFF: if the live latest revision timestamp < W start, the side whose revision equals it is right, the other wrong.
  - history MISSING_EXPORT: revision is live, visible, on the same page, and live sha1 equals the legacy text hash -> EXPORT_WRONG. Mirrored.
  - TEXT_DIFF: live sha1 of that revision decides (EXPORT_WRONG / LEGACY_WRONG / BOTH_WRONG); hidden sha1 -> UNCONFIRMED.
  - Else UNCONFIRMED (reported, not a defect).
- Descriptive integrity counters per file set (sha1 attribute vs computed hash, bytes vs length, missing text without deleted flag, empty text with nonzero bytes), duplicate keys, max revision timestamp per side.

## 6. Frozen verdict rules
- INVALID: >4 of 32 sampled wikis unusable (no comparison after one retry; recent changes not covering W; a revision timestamp >= W end on either side).
- CONTINUE: live-confirmed export-side defects in >=2 sampled wikis (current arm), OR >=100 confirmed export-side defects in any single arm-wiki (sample or T), OR confirmed export-side defects in >=2 history-arm wikis.
- CHANGE: any confirmed export-side defect below the CONTINUE bar, or only legacy-side confirmed defects.
- STOP: zero confirmed export-side and legacy-side defects in every arm.

## 7. Resources: host CPU, Python stdlib, <=25 GB download, <=6 h, $0. Abort on HTTP 429, 5 consecutive failed downloads; checksum mismatch retried once then wiki unusable.

## 8. Limitations: one edition; wikis capped at 300 MB except T; history small wikis only; suppressed actions not in public recent changes (hence only live-confirmed defects count); from November the export deliberately omits suppressions via a 7-10 day buffer.
-----

Reply in this format:
P(CONTINUE)=..., P(CHANGE)=..., P(STOP)=..., P(INVALID)=...
Rationale: ...
Flaws:
1. ... Fix: ...
```

## Reply

P(CONTINUE)=0.40, P(CHANGE)=0.27, P(STOP)=0.18, P(INVALID)=0.15

Rationale: The export is a newer pipeline. As far as we know, it is built from reconciled data-lake content history, not the legacy dump code. It failed badly at scale only eight months ago (T417596), so residual gaps are plausible. They are most likely in history, imported or undeleted revisions, and unusual content models. A clean 5-page pilot says little about that. STOP is the hardest outcome because it also needs zero confirmed legacy-side defects, and legacy dumps have known quirks of their own. INVALID carries real weight because the "timestamp >= W end" rule assumes both sides were snapshotted before October 8, and nobody has measured that across the sample.

Flaws:
1. **Documented design differences can be counted as defects.** The sunset page lists "minor differences" between the two products. Possible examples are excluded namespaces or content models, the added `parentid`, a different handling of suppressed or deleted content, and redirects. These are not pre-classified, so a known design difference can fall through to UNEXPLAINED. It then passes live confirmation, for example "live latest equals legacy" leads to EXPORT_WRONG, and gives a false CONTINUE across many wikis. Fix: before freezing, copy every listed difference into a DOCUMENTED class with a precise rule. Report it separately and exclude it from the defect counts. Also group confirmed defects by root-cause signature so that one systematic cause is not counted as "≥2 wikis" by itself.

2. **The timing window W is assumed, not measured.** W starts September 28 on the assumption that neither snapshot is older. If the export (or the legacy dump) reads from a snapshot before September 28, or from a lagging replica, then edits between that snapshot and September 28 become UNEXPLAINED REV_DIFF. The live check would then label the stale side WRONG, which is a false confirmation. In the other direction, a snapshot after October 8 makes the wiki unusable and pushes toward INVALID. Fix: first compute each side's maximum revision timestamp (and maximum log-derived change) per wiki. Set a per-wiki window from just before the earlier snapshot to just after the later one, and pre-register the rule for that. Freeze only after checking the snapshot bounds on the full sample during design, and extend the INVALID rule to cover arms T and H.

3. **The live hash check has an encoding problem and multi-slot hashes, and it has no positive control.** MediaWiki's `rev_sha1` and the API `sha1` value are not guaranteed to match "SHA-1 hex of the main text". The dump stores sha1 in base36. For multi-slot revisions (MCR, such as Commons MediaInfo or wikis using slots), the revision sha1 is an aggregate over slots. Empty or legacy-null sha1 values exist for old revisions. Any of these can turn every TEXT_DIFF or history check into BOTH_WRONG, which currently counts as export-side, or into UNCONFIRMED. Fix: use the API `slots` with content and per-slot sha1, and compare the main-slot text after converting both to one encoding. Count BOTH_WRONG as its own class, not as an export defect. Add a positive control: plant known missing pages and altered text in a copy of one export, and require the classifier to return exactly EXPORT_WRONG for them before the main run.

4. **There is no comparator for the base rate of legacy-vs-legacy noise.** Without one, you cannot tell whether "UNEXPLAINED" differences come from the export or from the method itself. Examples are page-id changes from delete/undelete, moves over redirects, imports with old timestamps, and the RC coverage of log types such as merge, import and revision delete. Fix: run the same pipeline on legacy 20261001 against the next legacy edition, or against the live API, for a few sample wikis. Any non-zero "confirmed" rate there is method error and must be subtracted or fixed. Also key current pages by title as a fallback and record any page-id remaps.

5. **The sample cannot find the failure mode it is meant to test.** Most wikis under 300 MB compressed are tiny, the history arm is small wikis only, and the earlier failure appeared in a large wiki. Scale-dependent faults (partitioning, batching, reconciliation lag) may only show up in large wikis, and the frame drops all of them except enwiktionary-current. The history arm also has no fixed size and no INVALID rule. Fix: add a second large target wiki for current, add a capped history slice from a large wiki (a seeded random range of page ids), and freeze the size of arm H and its usability rule.

6. **Verdict asymmetries and sampling truncation.** "Seeded random 200 per wiki" is not extrapolated, so the threshold of ≥100 confirmed defects in one wiki depends on how the sample happened to fall. Legacy-only defects produce CHANGE, which blocks STOP even when the export is faithful, although the question asks about the export. The 134 missing closed wikis (arm C) never feed into the verdict, even though the "faithful replacement" claim may cover them. Fix: report confirmed rates with confidence intervals and base the per-wiki bar on the estimated count. Make STOP depend on zero export-side defects only, and report legacy-side defects descriptively. State explicitly whether missing closed-wiki directories count as a documented exclusion or as a coverage defect.
