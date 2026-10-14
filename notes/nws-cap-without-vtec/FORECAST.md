# Forecast (separate agent, before freeze; draft v1 sha256 c7939ba8…025c4, analyze.py v1 57f1f123…0879)

The forecaster was shown the draft protocol, not the snapshot. The forecast was not fully blinded to prior project context, so
contextual contamination cannot be excluded.

- P(CONTINUE) 0.70, P(CHANGE) 0.13, P(STOP) 0.05, P(INVALID) 0.12. p_adv (CONTINUE or CHANGE) = 0.83.
- Point predictions: P1 ≈ 96% (90–99%), P2r ≈ 75% (55–90%), P2f ≈ 2%.
- Main reason: EXP (and maybe CAN) likely arrive as `Update`, and EXP notices are often sent 10–60 min before the end, so a
  messageType + 10-min rule misses them.

Design changes adopted from its critique before freezing (v2):
1. Positive control named in the protocol and extended (UPG kept apart by R2, expiredReferences-only link, text-only end).
   An R0 no-edge floor added. Shuffle negative control not adopted (R0 is the floor).
2. Primary P1 restricted to events with ≥ 2 alerts; all-events and NEW ≥ 48 h sets reported as sensitivity.
3. End predictor widened to E2 = messageType OR time OR text, with E1/ET/EX reported separately; `expiredReferences` used as
   graph edges (they exist on 4,949 alerts).
4. Multi-VTEC alerts counted before freeze: 0 of 10,498, so per-key assignment cannot merge an UPG+NEW alert.
5. Listing gaps: all 912 missing referenced ids fetched via `/alerts/{id}` before the main run; unresolved ids counted.

The protocol author's own prior after v2 (not blind): P1 likely ≥ 95%; P2r is the uncertain part. p_adv 0.6.
