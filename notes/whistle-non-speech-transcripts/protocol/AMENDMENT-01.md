> Public copy. Internal tracking IDs, team names, host paths and internal follow-up routing were removed or reworded. Methods, arms, data, metrics and the decision rule are unchanged. The protocol was frozen before the main run.

# Amendment 01 (execution only; decision rule, arms, data and scorer unchanged)
2026-10-15 ~08:12 UTC. The first main job ran the six audio arms as parallel 1-thread processes in one 6-CPU container.
Whistle slowed from ~1.5 s to 78–103 s per speech utterance (CPU contention; moonshine/onnxruntime used ~3.6 cores despite
OMP_NUM_THREADS=1). Stopped by SIGTERM to the job runner (exit 79, container removed, every JSONL ends on a complete row).
Rows written then were kept (run.py resume): W_en 14, W_auto 14, T_tiny 96, T_base 40, M_tiny 100, VAD 1465.
Continuation: arms run one at a time with THREADS=6 in order VAD, W_en, T_tiny, W_auto, M_tiny, T_base, then TOOL arms.
Effect: per-clip `sec` for rows written under contention is not comparable; latency stays descriptive and is reported only
for rows from the sequential jobs. Texts are unaffected (the repeat gate checks determinism).
No outputs had been inspected beyond row counts and the two W_en speech rows shown by `tail` while diagnosing the stall.
