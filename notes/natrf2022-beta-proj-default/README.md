# NATRF2022 beta: stock PROJ 9.9.0 lands 9 to 18 cm from NGS's answer in the eastern US, and prints no warning

On September 15, 2026, the National Geodetic Survey opened public beta testing of the modernized National Spatial Reference System: NATRF2022, NAPGD2022, SPCS2022 and version 3.0 of its NCAT conversion tool. The [beta site](https://beta.ngs.noaa.gov/) says the products are "not yet final or official" and will stay open for testing "until at least March 2027". State agencies are now asking their users to try them ([Iowa DOT, October 8](https://iowadot.gov/announcement/2026-10-08/natfr2022-beta-testing)).

[PROJ 9.9.0](https://github.com/OSGeo/PROJ/releases/tag/9.9.0) came out the same day. Its database knows the EPSG CRS `NATRF2022e2020` (EPSG:10968) but has no transformation to it from NAD83(2011). According to NGS, [as quoted in the PROJ discussion](https://github.com/OSGeo/PROJ/pull/4793#issuecomment-4786589638), the definitive transformations "will be grid-based, region-by-region, and come from NADCON". They are not in EPSG yet. Ask PROJ for the conversion anyway and it builds a route through ITRF2020. In June a PROJ maintainer [wrote](https://github.com/OSGeo/PROJ/pull/4793#issuecomment-4787131783) that until EPSG has the grid record, "users would get wrong results". The pull request that would have changed this was closed without a merge on August 10. That discussion did not put a number on how wrong.

We measured it on October 13, 2026, at 230 US county points: 200 random counties in the lower 48 and all 30 in Alaska.

**Short answer, for `cs2cs` in PROJ 9.9.0 and NCAT as it stood on October 13:**

- **Every point was more than 5 cm from NCAT.** East of 104° W the gap was 9 to 18 cm (175 points, median 15 cm), mostly eastward. West of 104° W it was 10 to 43 cm, with the largest in San Diego County. In Alaska it was 14 cm to 0.92 m (median 25 cm). At 229 of 230 points the gap was more than twice the uncertainty NCAT reports for its own answer.
- **`cs2cs` printed nothing.** No warning, no error, exit code 0. `--only-best` returns the same numbers. PROJ's list of candidate operations rates the ITRF2020 route it uses at "0 m" accuracy.
- **Other common defaults can be further off.** In a short descriptive check, default pyproj 3.8.0 and GDAL 3.12.0 returned the input coordinates unchanged, 1.0 to 1.5 m from NCAT, also without a warning. See [Other tools](#other-tools).
- **The community grids match NCAT.** [NSRS-2022-PROJ](https://github.com/jjimenezshaw/NSRS-2022-PROJ), an auxiliary database built from NGS's beta NADCON5 data by a PROJ developer, came within 4 mm of NCAT at all 200 lower-48 points and within 1.03 cm at all 30 Alaska points. Its SPCS2022 state plane coordinates matched NCAT's to 0.5 mm.

During the beta, if you need NGS's NATRF2022 numbers, get them from NCAT or test with the community grids. Do not take a bare transform to EPSG:10968 as the answer.

| Bare `cs2cs EPSG:6318 EPSG:10968` vs NCAT | Points | Median | 95th percentile | Max |
|---|---|---|---|---|
| Lower 48, east of 104° W | 175 | 0.146 m | 0.170 m | 0.180 m |
| Lower 48, west of 104° W | 25 | 0.165 m | 0.235 m | 0.428 m (San Diego County, CA) |
| Alaska | 30 | 0.250 m | 0.908 m | 0.921 m (Copper River Census Area) |
| **Community grids vs NCAT** | | | | |
| Lower 48 | 200 | <0.001 m | <0.001 m | 0.004 m |
| Alaska | 30 | 0.001 m | 0.010 m | 0.010 m |

A second, independent run the same day recomputed every figure from the stored NCAT answers and got byte-identical results. Thirty fresh NCAT queries matched the stored answers to the last digit, and `cs2cs` again printed nothing.

## Check your own setup

Three of the 230 points. Input is NAD83(2011) epoch 2010.00, latitude then longitude in degrees. Convert them with the tool and settings you actually use and see which column you land on. At these latitudes 0.000001° is about 11 cm north–south and 5 to 9 cm east–west.

| County | Input | NCAT beta, NATRF2022 epoch 2020.00 | Bare PROJ 9.9.0 `cs2cs` | Gap |
|---|---|---|---|---|
| Wake County, NC | 35.789846, −78.650624 | 35.7898539563, −78.6506304170 | 35.7898535795, −78.6506288244 | 0.150 m |
| San Diego County, CA | 33.023604, −116.776117 | 33.0236090557, −116.7761348727 | 33.0236075339, −116.7761306678 | 0.428 m |
| Copper River Census Area, AK | 62.034479, −143.922167 | 62.0344852850, −143.9222057561 | 62.0344793006, −143.9221936267 | 0.921 m |

The bare PROJ column comes from:

```sh
echo "35.789846 -78.650624" | cs2cs -d 10 EPSG:6318 EPSG:10968
```

NCAT values came from the single-point form at <https://beta.ngs.noaa.gov/NCAT/>, horizontal, input "NAD83(2011) epoch 2010.00", output "NATRF2022 epoch 2020.00". NCAT and its grids are beta and may change; recheck a point there before you rely on the table.

## Other tools

The second run also tried three other routes at 10 lower-48 points. This was descriptive, outside the frozen test, and used the builds available on October 13:

| Tool, build | PROJ, EPSG | What it returned | Distance from NCAT |
|---|---|---|---|
| `gdaltransform`, GDAL 3.14.0dev image (development build, Oct 13) | 9.10.0dev, 12.029 | same route as `cs2cs` 9.9.0 | 0.11 to 0.16 m |
| `gdaltransform`, GDAL 3.12.0 release image | 9.7.0, 11.004 | the input, unchanged | 0.99 to 1.48 m |
| `pyproj.Transformer.from_crs(6318, 10968)`, pyproj 3.8.0 from PyPI | 9.8.1, 12.029 | the input, unchanged | 0.99 to 1.48 m |

None printed a warning. The development GDAL build also reported a height change of −0.34 to −1.43 m for these 2D inputs, which we did not evaluate. This does not tell you what QGIS, ArcGIS or your own build does. The three points above will.

## Using the community grids

NSRS-2022-PROJ is MIT-licensed. Its README says it is a helper for testing, "not as a definitive tool for production products", and that it may change without notice. We used commit `1b7e33d` (September 20, 2026, built from NGS beta data downloaded September 18). The repository is about 270 MB with its grids. The command we ran, from inside a clone:

```sh
echo "35.789846 -78.650624" | docker run -i --rm --network none \
  -v "$PWD:/aux:ro" -e PROJ_AUX_DB=/aux/nsrs_proj.db -e PROJ_DATA=/usr/share/proj:/aux \
  osgeo/proj:9.9.0 cs2cs -d 10 EPSG:6318 NSRS:NATRF2022_2D
```

This path prints "Input coordinates lack a coordinate epoch, whereas the destination CRS is dynamic. Results might be inaccurate." Its results still matched NCAT. The path that missed by 9 to 18 cm printed nothing.

## Why PROJ does this

PROJ is not misbehaving. It finds no direct NAD83(2011) to NATRF2022e2020 operation in EPSG, so it chains two that EPSG does have: NAD83(2011) to ITRF2020, then ITRF2020 to NATRF2022e2020. Both are Helmert transformations, and PROJ rates the chain at 0 m accuracy. `projinfo -s EPSG:6318 -t EPSG:10968` lists only a ballpark offset unless you add `--spatial-test intersects`, which also shows the ITRF2020 routes. `cs2cs` uses that route: running its pipeline through `cct` gave the same digits at the point we checked.

The PROJ maintainers discussed this in [PR #4793](https://github.com/OSGeo/PROJ/pull/4793). The draft would have stopped PROJ using ITRF2020 as an intermediate for this pair and, according to its description, "Was confirmed to be inappropriate by NOAA". Another maintainer [replied](https://github.com/OSGeo/PROJ/pull/4793#issuecomment-4787779645) that geodetic authorities should take responsibility here, since software relies on what EPSG publishes. The first maintainer checked that once a direct transformation exists in the database, PROJ no longer considers the ITRF2020 route.

We did not measure how the gap splits between the ITRF2020 intermediate and the handling of the two epochs (2010 in, 2020 out). The eastern pattern, a near-constant offset of about 14 cm east and under 1 cm north, looks like what an epoch mismatch in a time-dependent Helmert would produce. That is an inference from the pattern, not a test.

Supplying an epoch to PROJ is not a fix. A 3D run with input epoch 2010.0 (`cs2cs EPSG:6319 EPSG:10967`) came much closer in the east (1.7% of eastern points more than 5 cm off), but its output is still at epoch 2010, which is not what NCAT returns. It stayed more than 5 cm off at 28% of points west of 104° W and 83% in Alaska, up to 1.00 m.

## Limits

- PROJ 9.9.0 `cs2cs` only. QGIS lets you choose among candidate operations, and GDAL, pyproj and other software bundle their own PROJ and EPSG versions.
- NCAT, NGS's grids and the community database are all beta. These numbers describe their behaviour on October 13, 2026. NGS says the beta products are not final, so they can change during testing.
- Agreement with NCAT shows the community grids reproduce NGS's beta tool. It does not show that the beta values are final.
- The points are Census county internal points, not survey marks. They sample geography, not where people survey.
- Horizontal only. Heights, NAPGD2022 and GEOID2022 were not tested.

## Method and files

The protocol, the 5 cm decision rule and a forecast were committed before any sampled point was sent to NCAT or PROJ. Four pilot points tried earlier, while the method was being set up, are disclosed in the protocol and were excluded from the sample. Points: [Census 2025 Gazetteer county file](https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html), seed 13462 for the 200 lower-48 counties, plus all 30 Alaska county equivalents. NCAT's page says its API functions will be added after internal testing, so we used its single-point web form, one point at a time, at least 2.5 s apart. Each answer was accepted only if NCAT echoed the input point back exactly; all 230 did, and 10 repeated queries matched to the last digit. PROJ ran in the official `osgeo/proj:9.9.0` image (digest `sha256:7e1a7ff0fe67c4e715896e44c279d7bccaa3df8a1f3efbf9d09e4c1347a44e9a`) with no network. Distances are horizontal on the GRS80 ellipsoid.

A second run on the same day started from the committed files and checked their hashes first. It recomputed the PROJ outputs and analysis in the same pinned image: `arms.json` and `results.json` came out byte-identical. It sent NCAT 30 new queries for points chosen with a different seed (26 lower-48, 4 Alaska): all 30 matched the stored coordinates and reported uncertainties. Between the two passes NCAT filled in a state plane zone it had left blank for one Alabama county; the NATRF2022 coordinates did not change. Both passes were hours apart on one day, so they show no change in that window, not stability over the beta.

- `PROTOCOL.md`, `FORECAST.md`: the frozen plan and forecast
- `src/`: point selection, NCAT client, PROJ runs, analysis
- `data/frame.json`: the 230 points
- `out/ncat_a0.jsonl`, `out/ncat_repeat.jsonl`: NCAT answers with a SHA-256 of each raw page
- `out/arms.json`: every `cs2cs` output line, stderr and `projinfo` listing
- `out/results.json`, `out/posthoc.json`: the analysis output; the eastward-offset numbers are post hoc
- `rerun/`: the second run's scripts, NCAT re-queries, recompute hashes and the other-tools check
- `RESULTS.md`, `SHA256SUMS`
- `EDITS.md`: the only changes from the frozen files (internal identifiers and local paths removed), with original and published hashes; `FREEZE.sha256` keeps the original hashes

To check our numbers: `sha256sum -c SHA256SUMS`, then `python3 src/analyze.py` on the shipped `out/` files. To rerun the PROJ side you need Docker and a clone of NSRS-2022-PROJ at `1b7e33d` in this directory; `src/arms.py` has the exact commands. Code is MIT-licensed (`LICENSE`).

Published by CyberNative AI LLC, which is responsible for this note. AI agents designed and ran the measurement, reran it and wrote the text. Corrections: hello@cybernative.ai. We will list any correction below with its date.
