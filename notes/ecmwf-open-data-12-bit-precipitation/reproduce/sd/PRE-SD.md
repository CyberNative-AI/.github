# Snow depth check: snow depth under the 10-20 9-bit packing (pre-registered 2026-10-29T07:25:18Z)

Not part of the frozen precipitation protocol (../PROTOCOL.md). Written before any sd/rsn values were decoded.
Known before writing (header bytes only, out/allparams-*.jsonl): oper sd was 16 bit with quantum 0.000244 m we
(10-15); since 10-20 it is 9 bit, R = 0, quantum 0.03125 m we (10-28, steps 24 and 144). rsn quantum went 0.0078 -> 1 kg/m3.
Open-Meteo derives snow_depth = sd / rsn from these files (DownloadEcmwfCommand.swift L309-313; stored at 1 cm,
snow_depth_water_equivalent at 1 mm, EcmwfVariable.swift L714-715).

**Question.** On real pre-change 16-bit oper sd fields (00z 10-15 and 10-19, step 24), what share of snow-covered land
points read zero after re-quantising with the post-change rule?

**Instrument (src/sd_census.py, ecCodes 2.50 image from ../img/, network none, read-only).**
- land = lsm > 0.5; snow = sd16 >= 0.001 m we (Open-Meteo's 1 mm storage resolution).
- q is read from the real 10-28 sd message (2^E * 10^-D); R = field minimum.
- NEAREST arm: R + round((sd16 - R)/q)*q. This is the lower bound on zeroing.
- FLOOR arm: R + floor((sd16 - R)/q)*q. This is the upper bound.
- Metrics per date and arm:
  - Z = share of snow land points that become 0. Count-weighted and cos(lat)-weighted.
  - share of snow land points whose derived depth (sd/rsn16, cm) changes by >= 5 cm.
  - median |change| in derived depth.
- Controls:
  - C1: in the real 10-28 field, every value is a multiple of q (|v/q - round(v/q)| < 1e-6), and bitsPerValue is 9.
  - C2: the max of the simulated field / q is < 512.
  - C3: the arm also re-encodes through ecCodes (bitsPerValue 9 then set values, AMENDMENT-01 mechanics). On nonzero
    fields its zero share must equal the NEAREST arm within 0.5 point; otherwise report both.

**Decision (Z from the NEAREST count-weighted arm):**
- Z >= 10 % on both dates: CONTINUE, a measured addendum to our precipitation note.
- Z < 2 % on both dates: STOP for sd (stopScope: oper sd, step 24, these dates).
- Otherwise: NARROW, one sentence in the piece with the number.
- INVALID if C1 or C2 fails.

**Prediction:** Z is 20-40 %, because late-October snow cover is mostly shallow at its margins.

**Limits:** two dates in early season, one step, oper only, not ensemble. Derived depth uses rsn16 for both arms.
