# AMENDMENT-02 (2026-10-29 02:45Z): SIM12 gate code vs frozen text. Written AFTER results were seen.

**Disclosure.** This amendment was written after out/result.json existed and after its metrics had been read. It changes no metric, arm, threshold or decision rule. It reports one place where the frozen code did not implement the frozen protocol text, and it records the verdict under each.

**Frozen text (PROTOCOL.md, Gates):** "SIM12, the arm is real. Every **nonzero** SIM message has bitsPerValue 12, E(12) − E(16) ∈ {4, 5}, and max |SIM − ORIG| > 0."

**Frozen code (analyse.py, sha256 8b34233b…):** `ok = i12["nbits"] == 12 and (v.max() == 0 or (…))`. The zero exemption covers only the E/difference clause. The bitsPerValue == 12 clause is applied to zero messages too. ecCodes 2.50 encodes a constant field with bitsPerValue 0, so an all-zero message can never pass that clause.

**Census (src/sim12_census.py sha256 b5ed3f12c8b04373861df1dde6c325676bf25bacfdda06abdfbc89ffe3b3f633; same image, network none, read-only raw; output out/sim12-census.json sha256 7cab2153ffd87aa91121636e9d3b5894fbf762db67a8b8dcd736f920a187ff1f).** It applies the frozen predicate to every pre-change tp message:
- fail / zero: 102. These are the step-0 messages: 2 runs × (1 oper + 50 enfo). All are constant 0, bitsPerValue 0 before and after, and the values are identical to ORIG.
- ok / nonzero: 2520.
- fail / nonzero: 0.

So the code's SIM12 = false (2520/2622) comes entirely from messages that the text exempts. Step 0 is a zero accumulation in every arm, so these messages add nothing to any metric.

**Verdicts.**
- Frozen code, as printed in out/result.json (sha256 c2b09cff258ea76c06263cfd7af0bf75bd27a444b724d93b8c236adc69c829ae): **STOP_INSTRUMENT**. The file is not edited.
- Frozen protocol text: G1, G1b, G1c and G2 pass, and SIM12 passes on all 2520 nonzero messages. P1_SIM = 19.6 % (10-15) and 20.7 % (10-19), both ≥ 5 %. The verdict is **CLAIM_CONTRADICTED**.

**Which one we report.** The protocol text is what was frozen as the decision rule, and the code was written to implement it. We report CLAIM_CONTRADICTED and state in every carrier that it rests on this post-result correction of a gate implementation defect. An independent reviewer should re-derive SIM12 from the text and the census before any public use.
