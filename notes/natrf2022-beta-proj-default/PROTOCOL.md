# NAD83(2011) → NATRF2022 during the NGS beta: how far is stock PROJ's default from NGS's official tool, and does the open grid path match it?

Status: FROZEN 2026-10-13, v2 after a pre-freeze critique (see Freeze record), before any frame point is sent to NCAT or PROJ.
Risk tier 1: public NGS beta web tool (one point at a time, ≥2.5 s apart, ~230 + 10 form submissions), public
Census file, official PROJ image and a public MIT repository executed in CPU Docker `--network none`. $0. No outside contact.

## Why now (primary sources, fetched 2026-10-13)
- beta.ngs.noaa.gov/NCAT/ (NCAT 3.0 beta, "Last Updated: Oct 13 2026"): "Welcome to the beta release of the Modernized NSRS
  tools. These preliminary products are available for public testing and evaluation and are not yet final or official ...
  let us know about any issues you encounter, including file or syntax errors, unexpected computational results, API failures".
  NGS beta tools released 2026-09-15 (Iowa DOT notice 2026-10-08: six months of beta testing).
- PROJ 9.9.0 released 2026-09-15. Its proj.db contains EPSG NATRF2022e2020 (EPSG:10966/10967/10968, Gulf zones) but no grid
  transformation from NAD83(2011). `projinfo -s EPSG:6318 -t EPSG:10968 --spatial-test intersects` lists only the ITRF2020
  intermediate pipelines, a WGS 84 null path and a ballpark.
- OSGeo/PROJ PR #4793 (closed unmerged 2026-08-10) "Do not use ITRF2020 as an intermediate for NAD83(2011) to NATRF2022":
  "Was confirmed to be inappropriate by NOAA. They will publish grid based transformations"; maintainer: "we don't know when
  such record will land to EPSG, so in the meantime users would get wrong results". No magnitude was published there or on the
  PROJ list (2025-04-28 thread).
- Community aux DB github.com/jjimenezshaw/NSRS-2022-PROJ @1b7e33d (2026-09-20, MIT, by a PROJ developer): NADCON5 grids
  NAD83(2011)→NATRF2022 (CONUS, Alaska) built from beta.ngs.noaa.gov data of 2026-09-18.
- Pilot (4 points, seen before freeze, excluded from the frame and reported separately): stock default differed from NCAT by
  ~0.16 m (40N 80W), ~0.40 m (34N 118W), ~0.24 m (61N 150W); aux grid path agreed to 1e-10 deg at all 4.

## Question
For real US locations, (Q1) how far does stock PROJ 9.9.0's default NAD83(2011) → NATRF2022 result (what cs2cs, and
`proj_create_crs_to_crs` callers, get today without extra data) land from NGS's official beta NCAT result? (Q2) does the open
community grid path reproduce NCAT? (S3, descriptive) do the aux DB's SPCS2022 projections reproduce NCAT's state-plane values?

## Frame (fixed)
Census 2025 Gazetteer county internal points (`data/2025_Gaz_counties_national.txt`, sha256 1914f0d8…b35b1): seeded
(13462) random 200 CONUS counties + all 30 Alaska county-equivalents = 230 points (`data/frame.json`, sha256 1bc0f43e…36c39).
Coordinates are used as NAD83(2011) epoch 2010.00 test positions (realization of the Census source is irrelevant to parity).

## Arms
- A0 reference: NCAT beta single-point form, input "NAD83(2011) epoch 2010.00", output "NATRF2022 epoch 2020.00",
  horizontal, lat-lon (`src/ncat.py`, `src/collect.py`). The beta REST API `/api/ncat/llh` rejected every NATRF2022 output
  string tried ("Invalid outputDatum"); recorded as an observation, not part of the rule. Status per point: VALID (parsed
  output AND NCAT's echoed input equals the sent point to 1e-9 deg) / NA (NCAT shows explicit N/A output) / ERROR (HTTP,
  parse or echo failure after 3 attempts; raw HTML kept under out/raw_errors/).
- A1 stock default: osgeo/proj:9.9.0 (digest 7e1a7ff0…), `cs2cs -d 10 EPSG:6318 EPSG:10968`, no epoch, no grids, network none.
- A2 stock, epoch-aware user: `cs2cs EPSG:6319 EPSG:10967` with input epoch 2010.0, height 0 (output stays at epoch 2010.0;
  descriptive arm).
- A3 open grid path: same image, PROJ_AUX_DB = aux `nsrs_proj.db` @1b7e33d, PROJ_DATA += its grids,
  `cs2cs EPSG:6318 NSRS:NATRF2022_2D`.
- S3: NCAT's own NATRF2022 output → `NSRS:<zone>` (zone code = NCAT label prefix with spaces → `_`), compared with NCAT
  SPC northing/easting (m). Descriptive; unmapped zones counted.
Distance: local GRS80 horizontal distance (`src/analyze.py`).

## Frozen rule (applied by `src/analyze.py`, committed with this file)
Primary metric: share of VALID points with |A1 − A0| > 0.05 m (5 cm: above NCAT's own reported 1-sigma of ~2 cm and a
common survey/engineering tolerance).
- CONTINUE if share ≥ 25% (the default path is materially off across the frame).
- STOP if share < 5%.
- CHANGE otherwise (report regional pattern only).
- INVALID if any: an arm container exits non-zero or returns a line count different from the frame; ERROR > 5% of frame;
  C1 (10 seeded points re-queried after the main pass, seed 134620) has < 10 records or < 8 VALID pairs, or differs
  > 1e-10 deg on any pair (NCAT changed mid-run); fewer than 150 CONUS or 15 AK VALID points. The harness control is the
  per-point input echo. A1 points that cs2cs cannot transform (`*`) stay in the denominator and count as not > 5 cm.
- A3 disagreement with A0 is reported as a finding (NCAT vs the 2026-09-18 beta grids), not as INVALID.
Secondary (reported, no decision weight): medians/p95/max per stratum (CONUS west/east of −104°, AK); A1 share > 2×NCAT
sigma; A2 distribution; A3 share > 1 mm; S3 max |ΔN|,|ΔE| and count > 1.5 mm.

## Resources and abort
CPU only. NCAT ≤ 1 point per ~3 s (GET + POST), sequential; abort the collector if 5 consecutive ERRORs or any HTTP 429/403
(record and stop; no retries past 3 per point). PROJ arms: one container per arm, 1 GB memory, 10 min timeout. Wall ≤ 90 min.
Teardown: no containers left (`--rm`); aux copy kept until the rerun closes.

## Limitations (known before results)
- NCAT, its grids and the aux DB are beta; results describe 2026-10-13 behaviour only. EPSG may add the grid transformation
  (then PROJ prefers it when grids are reachable).
- A1 is the cs2cs default; GDAL/QGIS/pyproj builds may bundle other PROJ/EPSG versions and QGIS offers a choice of operations.
  Claims stay scoped to PROJ 9.9.0 cs2cs.
- County internal points are not survey marks; the frame measures geography, not usage.
- Executed on our own hardware; not independently reproduced until the rerun.

## Interpretation guard (epoch semantics)
NCAT answers "NAD83(2011) epoch 2010.00 → NATRF2022 epoch 2020.00", which includes 10 years of intra-frame motion. EPSG:10968 is
named "NATRF2022e2020", so a user who asks PROJ for that CRS asks the same question; the primary metric therefore measures the
gap a default user receives. It does not by itself apportion that gap between "ITRF intermediate" and "epoch handling". A2 and
the west/east split are descriptive only; any causal decomposition is post hoc. A3 matching A0 shows the open grids reproduce
NCAT, not that NCAT (a beta) is correct.

## Freeze record
- v1 written 2026-10-13 after 4 pilot points. Pre-freeze critique (separate agent, read-only) found: no abort code; parse
  failures counted as NA; unused input echo; A3 control conflating NCAT revisions with harness errors; no rc/line-count
  checks; C1 passing with nothing compared; sigma default 0; S3 key name. All fixed in v2 before any frame point was sent.
- Observation before freeze: NCAT's SPC block returned zone "PA W-421004" for (40, −80) at ~19:45Z and "N/A" for the same request
  at ~20:30Z with unchanged lat/lon output; the beta was changing on 2026-10-13. S3 runs only on points where NCAT returns SPC.

## Clarification appended 2026-10-13 (after review; the frozen entries above are unchanged)
- The "Observation before freeze" entry gives a second time of ~20:30Z. That is later than the protocol freeze (19:45:28Z)
  and later than the last main NCAT query (20:10:23Z), so its times cannot be right as written, and no raw NCAT page was kept
  for either request. Its times and its claimed SPC zone change are unverified. They are not used in any measured result.
- The supported SPC change is the Alabama county whose zone NCAT filled in between the main pass and the rerun
  (rerun/RERUN.md, rerun/ncat_requery.jsonl).
