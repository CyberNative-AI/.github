> Public copy. Internal tracking IDs, team names, host paths and internal follow-up routing were removed or reworded. Methods, arms, data, metrics and the decision rule are unchanged. The protocol was frozen before the main run.

# Amendment 02 (execution only)
2026-10-15 ~11:05 UTC. The descriptive arm T_base (Whisper base) was stopped by SIGTERM to the job runner at 889/2,312 rows
(last row intact), to free the shared machine for a second run from a fresh install. Per the protocol,
an interrupted arm is INCONCLUSIVE; it is not part of the verdict (W_en, T_tiny, VAD all complete). Resume is mechanical
(`run.py` skips written ids) and is scoped into that rerun. A main-seq1 container left in Exited state after its
runtime-ceiling stop was removed by hand (`docker rm`); no containers remain and no GPU compute process ran.
