# AMENDMENT-01 (2026-10-28 23:30Z): mechanics only

**What happened.** The first run of the frozen analyse.py (581d6524…, started 21:54Z) crashed on the first re-encode with `data_ccsds_packing unpack: aec_buffer_decode error -3` / `DecodingError: Decoding invalid`. In ecCodes 2.50, setting `bitsPerValue` on a grid_ccsds message does not repack the existing data. No product metric was computed, and no output other than the crash trace exists (out/ holds only RAW.sha256 and the job receipts).

**Mechanics test** (1 message: 2026-10-15 oper tp at 24 h). Setting bitsPerValue and then re-setting the values gives:
- 16 bit: identical values, E = −17.
- 12 bit: E = −13, maximum difference 0.500 of a 12-bit step (= rounding). The pilot's real post-change E at 24 h is also −13.

**Change.** `reencode()` now sets bitsPerValue and then re-sets the values. The G1c noise check sets bitsPerValue before the values (it had the reverse order). Metrics, arms, gates, thresholds and decision rules are unchanged.

New analyse.py sha256: 8b34233bf1f2ff23e56a54dac87e2c5c3c18dda109dd8a58e6c0dd82261dfb54
