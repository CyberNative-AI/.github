# Does ECMWF's 2026-10-20 cut to 12-bit precipitation change the rain products users compute from open data?

Status: FROZEN after one pre-freeze critique (read-only reviewer, 10-28; it found 2 flaws: gates that could not fail plus consistent tie rounding undercounting flips; and an all-land denominator. Both are fixed above). Freezes at the commit that adds FROZEN.sha256. Owner and executor: CyberNative AI LLC. Risk tier 0 (public open data, CPU only). $0.

## Claim under test (primary source, quoted)
ECMWF Confluence, "ECMWF open data: bits per value" (page 738041093, version 2026-10-20T09:27Z): "From 20 October 2026, every field is set by the precision it actually needs" … "tp | Total precipitation | surface | 12 | was 16" … "Is anything lost? Nothing that is used. The bits removed sit below the level at which each field carries meaningful information, so the values people read, and the fields they compute with, are unchanged to well within their own accuracy." … "The rounding is uniform and bounded at each grid point, with no bias or artefacts."

## Users and the product tested
Open-Meteo reads these files. Its `EcmwfOpenDataSource.swift` (main, read 2026-10-28) lists data.ecmwf.int and the AWS/Azure/Google mirrors for its `ifs025` and `ifs025_ensemble` domains. Its docs (open-meteo.com/en/docs, read 2026-10-28) say: "precipitation_probability … Probability of precipitation with more than 0.1 mm of the preceding hour. Probability is based on ensemble weather models with 0.25° (~27 km) resolution." Open data `tp` is accumulated from step 0, so window amounts are differences between steps. **Our window is the native file step (6 h), not Open-Meteo's interpolated hour.** We test the product family: threshold exceedance of a differenced amount. This is not a replication of Open-Meteo's exact pipeline.

## Pilot (before freeze; no products computed)
GRIB section 5 of oper tp. On 2026-10-15, 16 bit: E = −17 at 24–120 h, −16 at 168–312 h, −15 at 360 h (steps 0.008, 0.015, 0.031 mm). On 2026-10-28, 12 bit: E = −13 at 24 h, −12 from 72–360 h (0.122, 0.244 mm). Files: `out/pilot-tp-sec5.txt`.

## Design: same weather, two encodings
Inputs are ECMWF open data, IFS 0.25°, 00z, Google mirror (`storage.googleapis.com/ecmwf-open-data`). Byte ranges come from the published `.index` files and are kept locally with sha256 (out/RAW.sha256).
- **Pre-change runs (main arm):** 2026-10-15 and 2026-10-19 (the last full day before the change; chosen before any decoding). Streams: oper fc `tp` at steps 0–144 by 6 and 150–360 by 6, plus `lsm` (land = lsm > 0.5); enfo ef `tp` for the 50 perturbed members at 0–144 by 6.
- **ORIG** = the 16-bit values as published.
- **SIM** (lower bound) = the same message re-encoded by ecCodes 2.50 (`bitsPerValue=12`, same CCSDS packing, ecCodes picks the binary scale and reference). Rounding is consistent: an ORIG accumulation that does not change between steps cannot flip, so SIM **undercounts** flips where the true increment is smaller than one 16-bit step.
- **SIM_DITHER** (upper bound) = each nonzero ORIG value plus independent seeded U(−q16/2, +q16/2) dither per message, clipped at 0, then rounded half-up onto the grid ecCodes chose. This **overcounts**: it treats every unchanged nonzero accumulation as possibly changed by less than q16.
- The verdict uses SIM to show a change and SIM_DITHER to rule one out (Decision).
- **Post-change run (real-data arm, descriptive):** 2026-10-28, same streams, actual 12-bit files. It reports negative increments and the E per step. Different weather, so it is not compared with the pre-change runs for an effect size.

## Metrics (src/analyse.py → out/result.json)
Land grid points only (lsm > 0.5 from the run's own oper step-0 file). Window amount A = tp(t) − tp(t − w).
- **P1 (primary, ensemble PoP, 0.1 mm):** PoP = share of the 50 members with A > 0.1 mm per 6 h window (24 windows to 144 h). ΔPoP = PoP_arm − PoP_ORIG, same members. Denominator: **uncertain point-windows**, i.e. 0 < PoP < 1 in ORIG or in the arm (dry or certain-rain points can't change). P1 = the share of uncertain land point-windows with |ΔPoP| ≥ 0.10. The 10-point bar is a chosen display-scale change (forecast apps commonly show PoP in tens). It is a judgement, not derived from sampling error: ΔPoP compares the same members, so it has none.
- **P1c (contrast, 1 mm):** the same at A > 1.0 mm. This sits above one 12-bit quantum (0.244 mm), so it shows whether any effect is confined to thresholds below the quantum.
- **Mechanism count:** the share of ORIG wet member-windows (> 0.1 mm) whose amount is below one 12-bit quantum.
- **Bias:** the mean signed ΔPoP on the uncertain set (SIM, 0.1 mm), with a 95 % bootstrap CI over the 48 windows of both runs (seed 17504, 2000 resamples). ECMWF says "no bias". A CI that excludes 0 contradicts that sentence for this product, and is reported as such.
- **P2 (negatives):** the share of land member-windows with A < 0, for ORIG, SIM and SIM_DITHER. Real post-change arm: the share in the actual 2026-10-28 files.
- **P3 (deterministic, oper):** 6 h wet/dry flips at > 0.1 mm divided by ORIG wet 6 h land windows (to 144 h). Also reported: 24 h flips at > 0.1 mm and > 1.0 mm (days 1–15), and the maximum |A_arm − A_ORIG|.

## Gates (in code; `gate_ok` in result.json)
- **G1, identity.** Re-encoding each pre-change message at its own 16 bits returns identical values and E. This can only fail through an encoder fault.
- **SIM12, the arm is real.** Every nonzero SIM message has bitsPerValue 12, E(12) − E(16) ∈ {4, 5}, and max |SIM − ORIG| > 0. G1 or SIM12 failing → STOP `stopScope=instrument`.
- **G1b/G1c, rule.** A numpy round-half-up on ecCodes' chosen grid equals ecCodes' 12-bit output, on ORIG (G1b) and on ORIG plus off-grid noise (G1c, which really tests the rounding rule). A failure means SIM_DITHER's rule is not ecCodes'. That is reported, and the HOLDS branch is then not available.
- **G2, consistency (weak).** Re-encoding the real post-change 12-bit messages at 12 bits returns them unchanged for ≥ 99 % of messages, otherwise INCONCLUSIVE. Values already on grid can't test how ECMWF chose E or the reference from full precision. That is a stated limit, and the modal E per step (SIM vs real post-change) is reported beside it.
- **Asserts:** exactly one oper tp per step; enfo members are exactly 1–50; the grid size equals the lsm size. Any fetch failure or missing step aborts the run.
- Limits: 4 CPUs, 8 GB, network none, 2 h wall per container run.

## Decision (frozen, computed in code)
- **CLAIM_CONTRADICTED** (Content gets a measured finding) if, in **both** pre-change runs, P1_SIM ≥ 5 % **or** P3_SIM ≥ 5 %. SIM is the lower bound, so this cannot come from the dither assumption.
- **CLAIM_HOLDS** (STOP, `stopScope` = "tp 16→12 bit; PoP > 0.1 mm/6 h and wet/dry > 0.1 mm on IFS 0.25° open data, two Oct-2026 00z runs") if, in both runs, P1_DITHER < 0.5 % and P3_DITHER < 0.5 %. The upper bound must be small.
- **MIXED** otherwise. Magnitudes and the bias CI are reported, with no public "contradicted" claim.
- G1/SIM12 fail → STOP_INSTRUMENT; G2 fail → INCONCLUSIVE.

## Known limits (written before results)
- ORIG is 16-bit, not full precision. SIM and SIM_DITHER bracket the double-rounding effect, and only SIM can support CONTRADICTED.
- Two runs from one season (October), 00z only, 0.25° only. The 0.1° tier and AIFS are not tested. Other parameters (2t at 9 bits, 10fg at 10 bits, sf) are not tested.
- 6 h windows, not Open-Meteo's interpolated hourly values or its exact post-processing (clamping negatives, interpolation).
- "Within their own accuracy" is not scored against observations. We test whether threshold products change, not forecast skill.
