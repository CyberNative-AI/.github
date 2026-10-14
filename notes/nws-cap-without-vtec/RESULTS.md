# Results: CAP without VTEC (api.weather.gov snapshot 2026-10-06..13)

> **Historical record, as written on 2026-10-13.** Several interpretations below are superseded by the dated correction at
> the end of this file (2026-10-14). Frozen thresholds, numbers and machine outputs are unchanged.

Status: Executed 2026-10-13 on our host (frozen protocol in this directory; `python3 src/test_analyze.py && python3 src/analyze.py raw out`
after `tar -xJf raw-snapshot.tar.xz`). Second run 2026-10-14: see `rerun/REPORT.md` (recompute byte-identical; it corrects "segments of one product" below to 107 of the 131). Raw machine output: `out/results.json`.

## Frozen ruling: CONTINUE
Driven by P1 alone. Inputs: 10,498 Actual alerts, 10,006 operational VTEC strings, 0 parse failures, 0 multi-VTEC alerts.

| Metric (frozen) | Value | Threshold |
|---|---|---|
| P1: EXACT grouping under R2, events with NEW in window and ≥2 alerts | **709 / 913 = 77.7%** (204 SPLIT, 0 MERGED) | CONTINUE if < 95% |
| P2r: recall of end predictor E2 (10 min) on CAN/EXP/UPG alerts | 1,522 / 1,531 = 99.4% | ≥ 99% |
| P2f: false-end rate on other VTEC alerts | 232 / 8,474 = 2.7% | between 1% and 5% (CHANGE band) |

Sensitivity (pre-registered): all NEW events 1,728/1,932 = 89.4% (single-alert events are trivially exact); ≥2 alerts and NEW
≥48 h before snapshot end 594/755 = 78.7%; excluding gap-touched events 709/913 (no primary event referenced any of the 911
ids the API no longer serves). R1 (no event/sender filter) gives the same 709/913; R2a (without `expiredReferences`)
577/913 = 63.2%; R0 floor 0/913. So `expiredReferences` matters, and the event/sender filter never had to cut a merge.

By phenomena (R2, EXACT/total): short-fused warnings are all exact — SV.W 88/88, TO.W 57/57, FF.W 71/71, FA.Y 90/90,
MA.W 34/34, FL.W 35/35. Failures sit in long-running zone-based hazards: SC.Y 44/122, GL.W 7/23, CF.Y 19/30, TO.A 5/13,
FA.A 27/33, WI.Y 34/39, FG.Y 27/31, HW.W 9/12 (full table in `out/results.json`).

End detection: messageType alone (E1) catches only 1,026/1,531 = 67.0% with 0 false ends (EXP arrives as `Update` 373 times
and as `Alert` 115 times; CAN as `Alert` 15 times). The text rule (EX) alone 80.5%; time rule (ET) alone 29.5%. The 99.4%
needs the text rule, so it depends on NWS wording; the 2.7% false ends come from the same text rule.

Watch numbers (S3, descriptive): the VTEC ETN appears as "WATCH n" in headline/NWSheadline/description for 56 of 87
TO.A/SV.A alerts; 31 carry no watch number outside VTEC.

## Post hoc (after the ruling; `src/posthoc_splits.py`, `src/posthoc_counts.py`, outputs in `out/`)
Why events split:
- 131 / 204: only parallel NEW roots. The event's first issuance was several segments, each a separate CAP `Alert` with no
  link to its siblings. Each piece is internally consistent; the shared event identity exists only in VTEC.
- 73 / 204: a chain restart. Every VTEC EXA/EXB alert (event extended to new zones) in the week — 212 EXA + 142 EXB = 354
  — is `messageType: Alert` with no `references` and no `expiredReferences`. Without VTEC, an area extension is
  indistinguishable from a brand-new event.
- All other action types carry references (CON 4,994/4,999; EXT 650/650; EXP 488/488; CAN 763/763; UPG 280/280).

## What this supports, and what it does not
Supported: in today's CAP stream, removing VTEC loses event identity for multi-segment issuances and for area extensions
(about 22% of multi-alert events in this week, concentrated in marine/coastal/wind/watch products), and leaves ending
detection dependent on free-text wording. Short-fused warnings track cleanly through CAP references.
Not supported / limits: one October week (few winter or tropical events); the stream is generated from VTEC today, and NWS
says future CAP will add event tracking, so this measures what today's format lacks, not what the future feed will be.
R2 is one consumer rule. The listing may omit alerts (911 referenced ids returned 404, none in primary events).
Executed on our host; independent rerun pending.

## Implication (for owners to decide)
A VTEC-free CAP needs (1) an event identifier shared across segments and across EXA/EXB extensions (ETN-equivalent), and
(2) an explicit end/expire marker that does not depend on wording. Those two concrete, measured requirements are an
increment to the NWS comment process (closes 2026-11-20).

## Correction (2026-10-14)

This correction supersedes the interpretations above where they differ. Numbers, thresholds and `out/*.json` are unchanged;
the corrected public summary is `README.md`, and the second run is `rerun/REPORT.md`.

- **Units.** The sample is 10,498 Actual alerts returned by the api.weather.gov `/alerts` listing for 6-13 October 2026
  (UTC), plus one referenced alert fetched separately; the listing may omit alerts. P1 is 709 of 913 **evaluated VTEC event
  keys** (77.7%): keys with a VTEC NEW alert in the snapshot and at least two collected alerts, grouped by one rule (R2:
  `references` and `expiredReferences` link two alerts only when both are known and share `event` and `senderName`).
  "Multi-alert events" and "about 22% of multi-alert events" above should be read as these 913 evaluated keys. "0 MERGED"
  applies within those 913 keys.
- **Warning classes.** "Short-fused warnings" and "long-running zone-based hazards" are not defined or tested classes. The
  measured results are per VTEC phenomenon and significance: SV.W 88/88, TO.W 57/57, FF.W 71/71, MA.W 34/34, FL.W 35/35,
  FA.Y 90/90 exact; SC.Y 44/122, GL.W 7/23, CF.Y 19/30, TO.A 5/13 and the others listed in `out/results.json`.
- **The 131.** In 131 of the 204 split event keys, each separate reference chain began with a VTEC NEW alert. These roots
  were not necessarily issued together or in one product: 107 are same-product-signature and 24 differing-product-signature
  cases (signature = AWIPS identifier, WMO identifier and `sent`). "The first issuance was several segments" and "the shared
  event identity exists only in VTEC" above are superseded.
- **Extensions.** All 354 area-extension alerts (VTEC EXA/EXB) in the listing snapshot were `messageType: Alert` and had
  neither `references` nor `expiredReferences`. That is the observed fact; "indistinguishable from a brand-new event" above
  claims more than the one grouping rule tested and is superseded.
- **Other actions.** "All other action types carry references" is superseded: CON 4,994 of 4,999 (5 unlinked), EXT
  650/650, EXP 488/488, CAN 763/763, UPG 280/280 carried `references` or `expiredReferences`.
- **Endings.** These are alert units. `messageType: Cancel` identified 1,026 of 1,531 alerts marked VTEC CAN, EXP or UPG
  (67%). None of the 488 listing alerts marked VTEC EXP used `Cancel`: 373 were `Update` and 115 `Alert`. E2 (messageType,
  a 10-minute end-time check and text matching) reached 99.4% recall on CAN/EXP/UPG alerts, with a 2.7% false-end rate
  among the 8,474 other operational VTEC-bearing listing alerts. This does not establish that every reliable detector needs
  those inputs; "leaves ending detection dependent on free-text wording" above is superseded.
- **Supported / implication.** The "Supported" and "Implication" paragraphs above are scoped to this one grouping rule
  against these 913 evaluated keys in one week of today's VTEC-derived feed. VTEC event keys can themselves group different
  products, zones or issuance times (`rerun/REPORT.md`). The independent rerun is no longer pending: see `rerun/REPORT.md`.
