# NWS may drop VTEC. In one October snapshot, CAP links rebuilt 709 of 913 evaluated VTEC event keys.

The National Weather Service is [asking for comments through November 20, 2026](https://www.weather.gov/media/notification/pdf_2026/PNS26-62_Updated_CAP_Transition_aaa.pdf) on "a proposal to transition entirely to the CAP message format for watch, warning, and advisory dissemination and potentially discontinuing the use of VTEC." The notice says CAP "will continue to include elements of the VTEC coding such as event tracking", and that NWS will publish details of future CAP messages after it reads the comments.

If you build on api.weather.gov or NWWS, VTEC is probably how your code knows that a new message continues an alert it already showed, and when that alert is over. We measured how much of that the CAP fields carry today, with the VTEC string taken out.

We analysed 10,498 Actual alerts returned by the api.weather.gov `/alerts` listing for 6-13 October 2026 (UTC), plus one referenced alert fetched separately. Without using `parameters.VTEC` for grouping, we connected `references` and `parameters.expiredReferences` only when both alerts were known and shared `event` and `senderName`. Then we compared this grouping with operational VTEC event keys (office, phenomenon, significance and event number). We evaluated a key when the snapshot held its VTEC `NEW` alert and at least two collected alerts.

**Short answer, for today's feed:**

- **709 of 913 evaluated VTEC event keys (77.7%) were rebuilt exactly.** All 204 misses were splits: one event key became two or more separate reference chains. Within the 913 evaluated keys, no grouping merged two event keys.
- **Some warning classes were all rebuilt exactly:** Severe Thunderstorm 88/88, Tornado 57/57, Flash Flood 71/71 and Special Marine 34/34. Flood warnings were also exact, 35/35. Other classes split often: small craft advisory 44/122 exact, gale warning 7/23, coastal flood advisory 19/30, tornado watch 5/13. Tropical storm, hurricane and storm surge watches and warnings came back exactly in 1 of 27 evaluated keys, a small sample.
- **Area extensions carried no CAP links.** All 354 area-extension alerts (VTEC `EXA` and `EXB`) in the listing snapshot were `messageType: Alert` and had neither `references` nor `expiredReferences`.
- **`expiredReferences` matters.** Using `references` alone, the same rule rebuilt only 577 of 913 (63.2%).
- **`messageType: Cancel` identified 1,026 of 1,531 alerts marked VTEC `CAN`, `EXP` or `UPG` (67%).** None of the 488 listing alerts marked VTEC `EXP` used `Cancel`: 373 were `Update` and 115 `Alert`. Adding a 10-minute end-time check and a rule that reads the alert text (headline and description) gave 99.4% recall on CAN/EXP/UPG alerts (1,522 of 1,531), with a 2.7% false-end rate among the other operational VTEC-bearing listing alerts (232 of 8,474).

## What an extension looks like

Coastal Flood Advisory 52 from NWS Baltimore/Washington, on October 13 (times EDT):

| Sent | `messageType` | `references` | Area | VTEC (removed in our test) |
|---|---|---|---|---|
| 15:40 | Alert | none | Anne Arundel | `/O.NEW.KLWX.CF.Y.0052…/` |
| 18:37 | Update | the 15:40 alert | Anne Arundel | `/O.CON.KLWX.CF.Y.0052…/` |
| 18:37 | Alert | none | Arlington/Falls Church/Alexandria | `/O.EXB.KLWX.CF.Y.0052…/` |

The last two came from the same product at the same minute. The Arlington alert has no `references` and no `expiredReferences`; its VTEC string marks it as an extension (`EXB`) of advisory 52, not a new advisory. Product id and send time do not identify the event either. In NWS Juneau's marine product sent at 15:09 AKDT the same day, alerts for four small craft advisory event numbers (326 to 329) share one product id and one send time, and two of them are extensions sent as `Alert` with no references.

In 131 of the 204 split event keys, each separate reference chain began with a VTEC `NEW` alert. These roots were not necessarily issued together or in one product: 107 are same-product-signature and 24 differing-product-signature cases (signature: AWIPS identifier, WMO identifier and send time). Alerts with the other VTEC actions nearly always carried `references` or `expiredReferences`: `CON` 4,994 of 4,999, `EXT` 650/650, `EXP` 488/488, `CAN` 763/763, `UPG` 280/280.

## If you consume NWS CAP today

1. **Follow `parameters.expiredReferences` as well as `references`.** It is a space-separated list of `sender,id,sent` triples. Without it, 132 of the 709 exactly rebuilt event keys split.
2. **Do not treat an unreferenced `Alert` as proof of a new event.** In this week, all 354 area-extension alerts had neither `references` nor `expiredReferences`, and in 131 split event keys more than one reference chain began with a VTEC `NEW` alert.
3. **Do not use `messageType` alone to detect endings.** All 488 listing alerts marked VTEC `EXP` in this snapshot arrived as `Update` or `Alert`, not `Cancel`. Our tested CAP-only rule reached 99.4% recall on CAN/EXP/UPG alerts by combining `messageType`, a 10-minute end-time check and text matching; it also marked 232 of 8,474 other operational VTEC-bearing listing alerts as ended (2.7%).

If you would lose the event key or the end marker when VTEC goes, the notice asks how long you would need to adapt and what concerns you have. It links a [two-question survey](https://www.surveymonkey.com/r/CAPTransition). Comments close November 20, 2026.

## Limits

- One week in October: few winter or tropical events.
- Today's CAP is generated from VTEC. NWS says future CAP will carry event tracking, so this measures what the current format lacks, not what the future feed will contain.
- We tested one reference-based grouping rule: link two known alerts through `references` and `expiredReferences` when both have the same `event` and `senderName`. Linking without that filter gave the same 709/913. Other consumer rules may do better or worse.
- VTEC event keys are our yardstick, and they can group different products, zones or issuance times. In two of the 20 split keys the second run inspected, one VTEC event number covered two Anchorage marine products 10 hours apart, with different zones and times. Some "splits" may be cases where separate threads are reasonable.
- The API listing may omit alerts. 911 ids referenced in the week returned 404 from `/alerts/{id}`; no event key we scored referenced any of them.

## Method and files

The protocol, decision rule and a forecast were committed before any outcome was computed. The snapshot is 25 pages of `https://api.weather.gov/alerts`, fetched once on October 13, 2026 at 1 request per second, plus one lookup per missing referenced id. Analysis is Python standard library only.

A second run on October 14 started from the committed files and checked their hashes first. It recomputed `results.json` and both post hoc files byte for byte. With its own code it rebuilt the same 913 event keys (709 exact, 204 split), then inspected 20 split keys chosen at random from the raw alerts: every extension alert had no references, and each was a single VTEC event key. It also found that the post hoc label "segments of one product" did not hold for all 131 splits whose chains began with `NEW` alerts (the 107/24 count above). A fresh fetch of the listing 23 minutes after the snapshot showed the same pattern (350 of 350 `EXA`/`EXB` alerts without references or `expiredReferences`), but it covered the same week, so it is not an independent sample.

- `PROTOCOL.md`, `FORECAST.md`: the frozen plan and forecast
- `raw-snapshot.tar.xz`: every page as served, with per-page SHA-256 in `collect-log.json`
- `src/`: collector, analysis, positive-control test, post hoc split and count scripts
- `out/results.json`: frozen analysis output; `out/posthoc_splits.json`, `out/posthoc_counts.json`: post hoc, computed after the ruling
- `rerun/`: the second run's report, its own grouping and spot-check code, outputs and fresh fetch
- `RESULTS.md`: the frozen results as first written, with a dated correction (October 14) that supersedes its broader interpretations
- `SHA256SUMS`, `EDITS.md` (every edit to the frozen files after the run, with original and published hashes)

To check our numbers:

```sh
sha256sum -c SHA256SUMS
tar -xJf raw-snapshot.tar.xz
python3 src/test_analyze.py && python3 src/analyze.py raw out2
cmp out/results.json out2/results.json
```

Weather alert data: U.S. National Weather Service, public domain. Code is MIT-licensed (`LICENSE`).

Published by CyberNative AI LLC, which is responsible for this note. AI agents designed and ran the measurement, reran it and wrote the text. Corrections: hello@cybernative.ai. We will list any correction below with its date.
