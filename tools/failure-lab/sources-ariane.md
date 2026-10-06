# Source evidence and implementation limits

Primary document: ESA/CNES Inquiry Board, *Ariane 501 Inquiry Board report*, 19 July 1996.

- [Public HTML transcription](https://www-users.cse.umn.edu/~arnold/disasters/ariane5rep.html)
- [Public PDF mirror at MIT](https://ocw.mit.edu/courses/16-355j-software-engineering-concepts-fall-2005/91f1e550b30b00ad797293f430220f18_ari5fail_ful_rep.pdf)

Both were opened through native web search on 2026-10-03. Page references below use the PDF's physical pages, counting its first page as 1.

## Passage register

S1 — §2.1, PDF p5: BH is an alignment result related to horizontal velocity, rather than velocity itself. Its 64-bit float to 16-bit signed-integer conversion overflowed. This section also states that alignment served no purpose after lift-off.

S2 — §2.2, PDF p6: the workload target was 80%; seven variables were at risk. Four received protection; three remained unprotected, including BH. The report does not supply per-variable costs or six other names.

S3 — §2.2, PDF p6; §3.1(o), PDF p13: safety reasoning was faulty for BH. No evidence established use of trajectory data in that analysis. Ariane 4's early trajectory kept this variable within its limit.

S4 — §3.1(e–j), PDF pp11–12: backup failed at H0+36.7s; active failed approximately 0.05s later. Diagnostic information became flight input; nozzle commands caused disintegration at H0+39s and automatic destruction. §2.1, PDF p5, also places the backup failure in the preceding 72ms data cycle. Do not equate the two timing descriptions.

S5 — §4 R1, PDF p14: the Board recommended switching off the alignment function immediately after lift-off.

S6 — §2.2, PDF p7; §3.1(m), PDF p12: continued alignment supported late-hold restart on Ariane 4; Ariane 5 retained it for commonality. Verified in the public PDF on 2026-10-03.

## Implementation limits

Label costs, selectable anonymous variables, curves, magnitudes, playback scale, and counterfactual outcomes illustrative. Counterfactual outcomes must say only that this modelled failure is avoided, without promising a full mission outcome. Use H0 labels for sourced event times.

The HTML quotes 21 source words total: the two short S2 excerpts (8 words) and the S5 recommendation (13 words). Keep source locators linked to the report and use concise paraphrases elsewhere.

## Model-only choices

The HTML uses anonymous variables A–F plus BH, a 62% illustrative base load, illustrative protection costs, and illustrative Ariane 4/Ariane 5 peaks. These values do not come from the report. The requested “protect BH instead of E” pass case conflicts with the original illustrative E peaks of 110%/115% and the rule that any unprotected peak above 100% fails. To keep that specified test coherent, the final model uses 96%/98% for E. This is an explicit model adjustment, not a historical claim.

The report places the backup failure at H0 + 36.7 s, the active-unit failure about 0.05 s later, and also says the backup had failed during the preceding 72 ms data cycle. The UI preserves these as separate report statements; it does not equate the two intervals.

The initial state is undecided (no protections, alignment on); the as-flown mapping is available through its explicit load button and revealed after flight. Source S6 supplies the alignment trade rationale.
