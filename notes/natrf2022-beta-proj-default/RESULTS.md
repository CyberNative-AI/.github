# Results — frozen verdict CONTINUE (Executed; same-day rerun in rerun/RERUN.md)

Run 2026-10-13 under PROTOCOL.md v2. Raw: `out/ncat_a0.jsonl` (230 NCAT beta responses, sha256 of each
raw page), `out/ncat_repeat.jsonl` (C1), `out/arms.json` (cs2cs outputs, stderr, projinfo summaries), `out/results.json`
(`src/analyze.py` output). Post-hoc numbers are in `out/posthoc.json` and labelled below.

## Validity
- NCAT: 230/230 VALID (input echo matched every sent point, including Aleutians West at 179.62°E); 0 NA, 0 ERROR.
- C1: 10/10 repeats identical (max |Δ| 0.0 deg). Arms: rc 0, 230 lines each. No INVALID reason.

## Primary (frozen rule)
Share of points where stock PROJ 9.9.0 (`cs2cs EPSG:6318 EPSG:10968`, no grids, no epoch) lands > 5 cm from NCAT beta:
**230/230 = 100% → CONTINUE** (cut 25%). It exceeded NCAT's own reported 2σ at 229/230.

| A1 vs NCAT (m) | n | median | p95 | max |
|---|---|---|---|---|
| CONUS | 200 | 0.148 | 0.176 | 0.428 (San Diego Co.) |
| CONUS east of −104° | 175 | 0.146 | 0.170 | 0.180 |
| CONUS west of −104° | 25 | 0.165 | 0.235 | 0.428 |
| Alaska | 30 | 0.250 | 0.908 | 0.921 |

cs2cs printed **no warning** for A1 or A2 (stderr empty). The only epoch warning in the run came from the aux-DB arm.
`projinfo` without `--spatial-test intersects` lists only a ballpark; with it, the ITRF2020-intermediate pipelines are listed as
"0 m" accuracy and "time-dependent operation". A1's results are not the ballpark (that would be ~1.15 m off everywhere).

## Secondary (descriptive)
- A2, the epoch-aware user (3D, input epoch 2010.0; output stays at epoch 2010): median 0.011 m overall. East CONUS
  >5 cm at 1.7% of points; west 28%; Alaska 83% (max 1.00 m).
- A3, the community grid path (NSRS-2022-PROJ @1b7e33d): CONUS max 4.0 mm (p95 0.4 mm). Alaska median 1.0 mm,
  16/30 > 1 mm, 2/30 > 1 cm (max 1.03 cm, Southeast Fairbanks). No point > 5 cm.
- S3, SPCS2022: aux-DB projection of NCAT's own NATRF2022 output equals NCAT's state-plane northing/easting within
  0.5 mm (print rounding) at 227/227 points that NCAT returned a zone for (3 returned no zone).

## Post hoc (not in the frozen rule)
- East of −104° the A1 error is a near-uniform eastward offset: median ΔE +0.144 m, ΔN +0.007 m, range 0.09–0.18 m. A
  constant offset of that kind is what a time-dependent Helmert evaluated at an epoch other than the one NCAT uses would
  produce. That cause is an inference from the pattern. I did not test it.
- A2 closing most of the eastern gap while west/Alaska gaps remain fits "10 years of intra-frame motion not applied". That is
  also inference, not a measured decomposition.
- The A3 Alaska residuals (≤1.03 cm) fit an interpolation-method or grid-storage difference. I did not test this either.

## What this does and does not show
- Shows: on 2026-10-13, a user who asks stock PROJ 9.9.0 cs2cs for NAD83(2011) → "NATRF2022e2020" gets a result 9–18 cm away
  from NGS's beta answer across the eastern US, up to 0.43 m in California and 0.92 m in Alaska. No message is printed.
  Installing the community NADCON5 aux DB brings it to within 4 mm (CONUS) and 1.03 cm (Alaska).
- Does not show: what GDAL/QGIS/pyproj builds return; QGIS lets users choose an operation. It does not show that NCAT (a
  beta) is correct, or how the A1 gap splits between the ITRF intermediate and epoch handling. PR #4793's maintainers
  already expected "wrong results"; the new increment is the measured size, the missing warning and the open-path parity.
- Forecast check: P(CONTINUE) 0.85 forecast; outcome CONTINUE. Expected A1 median ~0.2 m, observed 0.15 m. Expected west >
  east: true but small for CONUS (0.165 vs 0.146), large for Alaska. Expected A3 exact: wrong in Alaska (mm–1 cm).
