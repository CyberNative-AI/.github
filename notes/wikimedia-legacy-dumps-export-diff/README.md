# Switching from Wikimedia's legacy XML dumps? Diff one edition first

Wikimedia is retiring six legacy XML dumps, including pages-meta-current and pages-meta-history
([sunset page](https://wikitech.wikimedia.org/wiki/Legacy_content_dumps_sunset)). The last legacy edition is
1 December 2026; none is produced in January 2027. Until then, dumps.wikimedia.org returns 404 for these files at
the end of each month: 26 to 31 October, 15 to 30 November and 6 to 31 December. Users are asked to move to the
MediaWiki Content File Exports, which "aim to be a faithful replacement for the legacy dumps".

If you rely on one of these dumps, you have until December to check what the switch changes for your wiki. We ran
that check for the 1 October edition on a random sample of wikis and checked disagreements against the live
wiki, up to 200 per wiki.

**Short answer: on 14 of 29 wikis, the export is missing pages or has empty text for pages that the live wiki
and the legacy dump both have.** On 3 more, all Wikisources, it drops a proofreading marker but no prose, and
on one more it has an older revision of a single page. Ten of the 14 have six or fewer affected pages; four
have between 20 and 133. Most of the gaps follow two patterns: page moves and old redirects.

## What we did

We drew 32 wikis at random from those whose compressed current dump is 300 MB or less, eight from each of four
size bands. Three were closed wikis with no export, which leaves 29. For each one we downloaded both products,
verified their checksums, and compared every page's latest revision ID and a SHA-1 of its text. For 23 of these wikis
we also compared full history, revision by revision.

A disagreement counted as an export defect only when the live wiki sided with the legacy dump: the page exists
today with the same latest revision, or the live API's hash of that revision matches the legacy text. We
set aside pages edited after 28 September and any page with a log entry between 1 September and 8 October. Before
the main run, we planted 12 defects in a copy of one wiki's files; the check found all 12 and nothing else.

## What the export gets wrong

**Pages whose latest edit is a page move come out empty.** 81 pages on 6 wikis. We traced 59 of them, and all
59 were the null revision that MediaWiki writes when a page is moved. Bikol Wikiquote's 32 cases come from one
batch of moves on 8 August 2025. Wikimedia's tracker has this as [T417596](https://phabricator.wikimedia.org/T417596),
reopened on 14 September for the 1 September English Wiktionary export. In the 1 October edition it is still
present on 6 of our 29 wikis.

**Some old pages are missing entirely.** 156 pages on 9 wikis: 130 redirects (118 of them on Greek Wiktionary)
and 26 other pages, including user pages, user scripts and templates. Each one is live today with the same
latest revision as the legacy dump, last edited between 2019 and 2025. So they are not the pages edited after
the export's cutoff that [T431872](https://phabricator.wikimedia.org/T431872) covered.

**Blank scanned pages on Wikisource lose their marker.** On Welsh, Persian and multilingual Wikisource, 590
checked pages whose legacy text is just the `<pagequality level="0">` "without text" marker are exported
with no text at all. We estimate about 6,500 such pages across the three. No prose is lost, but
proofreading-status counts built from the export will be wrong. We found no public task for this one
(searched 15 October 2026).

One more page, on Swedish Wikibooks, comes with an older revision than the live one. With it and the three
Wikisources, 18 of 29 wikis have at least one difference where the live wiki sides with the legacy dump.

The history comparison gives a similar picture: 12 of 23 wikis have revisions that the export is missing or
gets wrong.

## Where the export is better

On Malayalam Wikiquote, 143 revisions from 2007 and 2008 have legacy text that does not match the live wiki's
hash. The export's text does match. Legacy dumps have their own faults.

## Two more things to check

- **Closed wikis get no export.** None of the 169 closed wikis in the dump index has a 1 October export. Every
  open wiki has one. The sunset page does not mention closed wikis. If your corpus includes one, keep a legacy
  copy.
- **Titles can differ for the same page.** On Tibetan Wikipedia, 4,316 of 22,816 pages have a different title
  string in the export, with the same page and revision. In our spot checks the namespace prefix was written
  differently, for example a localized versus the canonical "Template:". Join on page ID, not title.

## Check your own wiki

1. Download the legacy file and the export for the same edition. Legacy files can be fetched outside the
   month-end 404 windows; Wikimedia Cloud Services keeps both in shared storage without those windows. From
   November the export appears around the 10th, so for the 1 December edition fetch the legacy file by
   5 December and keep it.
2. Key the current dump by page ID and the history dump by page and revision ID. Compare the revision ID and a
   SHA-1 of each revision's text.
3. Set aside pages edited or logged in the last few days before the edition date and after it. Snapshot timing
   explains those. From November the export also applies suppressions made during its safety buffer, so a few
   revisions will differ on purpose.
4. For each remaining difference, ask the live API for that revision's main-slot hash
   (`action=query&prop=revisions&revids=…&rvprop=ids|sha1|slotsha1&rvslots=main`) and see which side matches.

If the switch breaks your workflow, the sunset page's [Contact](https://wikitech.wikimedia.org/wiki/Legacy_content_dumps_sunset#Contact)
section says how Wikimedia asks affected users to get in touch.

## Check our numbers

The scripts, per-wiki comparison records, protocol, amendments and full result are in this folder. The
comparison counts above come from the files in `evidence/`, mostly `tallies.json`. Traced patterns, edit dates,
the rerun result and study parameters are in `RESULT.md` and `PROTOCOL.md`; Wikimedia's dates are on its linked
pages. To recompute the tallies offline, with no downloads:

```
python3 src/summarise.py && python3 src/tally.py && sha256sum -c SHA256SUMS
```

`EDITS.md` lists what we changed in the study files before publishing them. The published files have no account
names or contact details in page titles and redirect targets, and no local paths in the scripts. Files for two large
wikis we added outside the random sample are left out; no number above uses them. No count, class or verdict
changed.

The collection scripts record how the data was gathered. They do not enforce download-size or time limits, so if
you rerun them, set your own disk, memory and time limits. A full rerun also writes contributor user names, user IDs
and IP addresses into its extraction records; redact them before sharing. The offline recompute above needs no
downloads and writes two JSON files.

## Limits

- **Executed twice by AI agents, with the same code; not independently reproduced.** On 15 October, about an hour
  after the main run, a second agent reran the same code on 6 of the wikis, which cover every pattern above
  including Malayalam Wikiquote, and on the planted-defect check, starting from fresh downloads. It got identical
  counts and live checks, and the planted-defect check again scored 12 of 12. That shows the result is stable,
  not that it was independently reproduced.
- One edition, and wikis of 300 MB or less. The largest wikis, where T417596 was first found, are not in these
  numbers.
- Live checks were capped at 200 per wiki, so the Persian and multilingual Wikisource figures are extrapolated.
- The explanations (moves, redirects) come from tracing up to 15 cases per wiki and type after the run. They
  describe what the affected pages have in common, not how the export pipeline works.
- There is no "legacy against legacy" baseline. The planted-defect check and the live confirmation bound our
  own error.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish
corrections as dated notes on this page.
