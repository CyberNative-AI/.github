# Independent second run (frozen CONTINUE)

Run 2026-10-13/14 on our host, CPU only, stdlib Python, no Docker. Clean copy = the committed frozen files.

## 1. Recompute: MATCH
- FREEZE.sha256: all 9 entries OK (`raw-snapshot.tar.xz` 9addc942...49d).
- Clean-copy files identical (cmp) to the working tree: PROTOCOL, FORECAST, src/*, raw-snapshot.tar.xz, out/*.
- `tar -xJf raw-snapshot.tar.xz` then `python3 src/test_analyze.py` -> ok; `python3 src/analyze.py raw out2`.
- `out2/results.json` == `out/results.json` byte for byte, sha256 76be4bef...80e.
- `posthoc_splits.py` -> 27c942aa...204; `posthoc_counts.py` -> 526e956b...c3, both byte-identical to `out/`.

## 2. Independent spot check (own code, `src/spot_check.py`, not analyze.py): MATCH on (a) and (c); PARTIAL on (b)
My own R2 graph (references + expiredReferences triples, same event + senderName, both ends known) reproduces the headline:
913 evaluated events, 204 split, 709 exact. Sample: `random.Random(135030).sample(sorted(split_keys), 20)`. Note
`posthoc_splits.json` only lists 6 examples, so the split list came from my own derivation. Full read-out: `spot_check.out`.
- (a) MATCH. Every EXA/EXB alert in the 20 events (and all 354 in the week) has no `references` and no `expiredReferences`;
  every chain-restart root in the sample is such an alert.
- (c) MATCH. In all 20, every alert's `/O.` VTEC string carries the same office.phenomena.significance.ETN.
- (b) PARTIAL. 18/20 events have >=2 NEW roots. In 14 of them, all NEW roots share AWIPS id, WMO header and `sent`: separate CAP
  Alerts of one product. In 4 they do not: KTAE.HU.W.1009 (TCVTAE 23:00 + MWWTAE 23:03), KLIX.TR.A.1009 (TCVLIX 10:12 +
  MWWLIX 10:21), PAFC.SC.Y.1594 and .1599 (two CWFALU products 10 h apart; different zones and different VTEC begin/end times).
  The other 2 events were chain-restart cases with no parallel NEW roots. Population check (`spot_extra.out`) over all
  204 splits: 107 parallel NEW roots from one product, 24 parallel NEW roots from more than one product, 73 chain restarts.
  So RESULTS.md "131/204 only parallel NEW roots ... segments of one product" is right on the 131 but overstated on
  "one product": 107 of the 131. Within this grouping rule and these 913 evaluated VTEC event keys, the result is unchanged
  (709 exact, 204 split); the PAFC cases also show the ETN key lumping unrelated zones and times, so gold is not perfect there.

## 3. Fresh-window check (descriptive): MATCH on pattern, NOT an independent week
One pass, 25 requests, 1 req/s, User-Agent `https://cybernative.ai`, 2026-10-14T00:02Z (23 min after the original snapshot).
Rows 11,560; 10,552 Actual; 78 ids not in the snapshot, 24 snapshot ids gone. Only 0.7% of ids are new, so this is the same week.
- EXA/EXB with no references: 350/350 (EXA 212, EXB 138), all `Alert`. Among the 78 new ids: 0 EXA/EXB, so no new evidence on EXA/EXB.
- messageType per action (all, `fresh_counts.txt`): NEW Alert 2,517 (no refs); CON Update 4,804 / Alert 204; EXT Update 604 / Alert 45;
  EXP Update 372 / Alert 115; CAN Cancel 747 / Alert 15; UPG Cancel 278 / Alert 2; COR Update 4. Same as the original table
  within roll-off; rows with no references outside NEW/EXA/EXB: 5 CON (same 5 as before).
- To test outside the week, repeat `src/fetch_fresh.py` + `src/fresh_count.py` after the listing has rolled (about 2026-10-21 or later).

## Files (sha256 in SHA256SUMS)
fresh-raw.tar.xz (repacked for publication with neutral owner metadata; member files unchanged, see `../EDITS.md`), fresh_counts.txt, spot_check.out, spot_extra.out, src/{fetch_fresh,fresh_count,spot_check,spot_extra}.py
