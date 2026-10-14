# If NWS drops VTEC, does today's CAP alert stream still carry event tracking?

Status: FROZEN 2026-10-13 (v2 after a blind pre-freeze critique, see FORECAST.md), before any outcome is computed on the snapshot.
Risk tier 1: public api.weather.gov listing (25 page requests, 1 s apart, plus one `/alerts/{id}` request per missing
referenced id, 0.5 s apart, User-Agent "cybernative-research
(https://cybernative.ai)"); analysis is offline Python stdlib on host CPU. $0. No outside contact, no account.

## Why now (primary sources, fetched 2026-10-13)
- NWS Public Information Statement 26-62 Updated (2026-09-18, `weather.gov/media/notification/pdf_2026/PNS26-62_Updated_CAP_Transition_aaa.pdf`,
  sha256 e0551a4b…f8441): "We are seeking comments through November 20, 2026 on a proposal to transition entirely to the CAP
  message format for watch, warning, and advisory dissemination and potentially discontinuing the use of VTEC." and "CAP
  formatted messages are currently derived from the VTEC format." and "[CAP] will continue to include elements of the VTEC
  coding such as event tracking ... The NWS will provide additional proposal details including enhancements to future CAP
  messages after evaluating public comments." NWS asks "how long it will take to accommodate these changes, what concerns
  you may have".
- Existing public discussion: weather-gov/api discussion #871 (2026-09-12) only relays the notice; no measured analysis found
  by web search on 2026-10-13.
- Consumer jobs at stake: deduplicating/updating an alert in an app, knowing when it ends, and joining to other systems
  that key by VTEC event number (watch numbers, verification, archives).

## Question
In today's CAP stream (api.weather.gov `/alerts`, which NWS derives from VTEC), with the `parameters.VTEC` value removed,
can a consumer (P1) group alerts into the same events that VTEC defines, and (P2) tell when an event ends for the zones of
an alert? This measures what the current CAP format carries; it does not predict the future VTEC-free generator. A loss
here names what a VTEC-free CAP must add; no loss here supports NWS's statement for these two jobs.

## Data (fixed before analysis)
Snapshot `raw/page-000..024.json` (collect-log.json: per-page sha256), fetched 2026-10-13T23:39Z..~23:41Z by
`src/collect.py`: every alert the listing returned, 11,507 rows, 11,504 unique ids, sent 2026-10-06T15:39-08:00 ..
2026-10-14T02:37+10:00. Only `status == "Actual"` alerts are used. Seen before freeze (instrument checks, disclosed):
page-000 field names; on page-000, VTEC strings per alert were 0 (80) or 1 (420) and messageType Alert 238 / Update 234 /
Cancel 28; the full snapshot had 1,008 non-Actual rows. Structural checks after the forecast: 10,498 Actual alerts, 0 carry
more than one VTEC string; `parameters` include `expiredReferences` (4,949 alerts; space-separated "sender,id,sent" triples)
and `eventEndingTime`; 912 distinct ids referenced by Actual alerts (references + expiredReferences) are absent from the
listing. No reference graph, outcome or action/messageType cross-tab was computed before freeze.
Gap fill (`src/fetch_missing.py`, before the main run): each missing id is fetched from `/alerts/{id}` into `raw/extra/`
(hashes in `raw/extra-log.json`); fetched Actual alerts join the graph as nodes and purity labels; ids still unresolved
are counted (`unresolved_referenced_ids`). Result of the gap fill (before freeze): 1 of 912 returned 200, 911 returned 404 (rolled off),
so a sensitivity set excludes primary events whose alerts reference any unresolved id ("gap-touched").

## Gold and evaluation set
Gold event key = VTEC office.phenomena.significance.ETN, operational (`/O.`) strings only (year omitted: one-week window
inside 2026). Primary evaluated events: every key with a `NEW` action in the listing snapshot (began inside the window) AND
at least 2 alerts (single-alert events are trivially grouped). Sensitivity sets: all NEW events; ≥2 alerts with NEW ≥48 h
before the last snapshot alert; primary minus gap-touched events. Unparseable VTEC strings are counted.

## CAP-only reconstructions (never read VTEC)
Edges come from CAP `references` plus `parameters.expiredReferences` (both CAP-native, not VTEC).
- R0 (floor): no edges.
- R1: connected components over all edges (unresolved ids kept as nodes).
- R2 (primary, the strongest simple CAP-only rule): edges only where both ends are known (snapshot or fetched) and have the
  same `event` and `senderName`.
- R2a (descriptive): R2 without expiredReferences edges.
An event is EXACT under a rule iff all its alerts fall in one component and no alert in that component carries another
VTEC key; otherwise SPLIT, MERGED or SPLIT+MERGED.

## End detection (P2)
Per operational VTEC-bearing listing alert: ending action = CAN, EXP or UPG. Primary CAP-only end predictor E2:
`messageType == "Cancel"` OR (`ends`, else `expires`) ≤ `sent` + 10 min OR the text rule (headline + NWSheadline +
description, upper-cased, regex `END_TEXT_RE` in `src/analyze.py`: "HAS/HAVE (BEEN) EXPIRED/CANCELLED/ALLOWED TO EXPIRE",
"WILL (BE ALLOWED TO) EXPIRE", "IS/ARE CANCELLED"). Descriptive: E2 at 0 and 30 min; E1 messageType only; ET time only;
EX text only.

## Frozen rule (`src/analyze.py`, committed with this file; positive control `src/test_analyze.py` must pass)
P1 = EXACT share under R2 on the primary set. P2r = recall of E2 (10 min) on ending alerts; P2f = false-end rate on non-ending alerts.
- CONTINUE (material loss) if P1 < 95% OR P2r < 95% OR P2f > 5%.
- STOP (today's CAP carries tracking for these jobs; NWS statement supported here) if P1 ≥ 99% AND P2r ≥ 99% AND P2f ≤ 1%.
- CHANGE otherwise (report which job and which phenomena fail).
- INVALID if: < 5,000 Actual alerts; < 500 evaluated events; VTEC parse failures > 1%; < 100 ending alerts (in
  `decide()`); or the positive control `src/test_analyze.py` fails (synthetic exact/split/merged/UPG/expiredReferences/
  text-end cases with known answers; run before the main analysis).

## Descriptive (no rule)
R0/R1/R2a outcomes; sensitivity sets; outcomes by phenomena.significance; action × messageType table; S3 = whether the VTEC event number appears in
headline/description/NWSheadline as "WATCH n" (watches TO.A/SV.A vs others); counts of multi-VTEC alerts.

## Limitations stated in advance
One October week (few tropical/winter events); NWS's own listing may omit alerts; R2 is one reasonable consumer rule, not
the best possible; today's references are produced by a VTEC-driven generator, so a future CAP-only generator may behave
differently in either direction. Executed on our host, not independently reproduced.

## Stop / next
Decision recorded the same day. Independent rerun of `src/analyze.py` on the hashed snapshot before any outside use.
