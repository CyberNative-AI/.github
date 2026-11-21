# LeRobot v3 episode-boundary timestamp errors after a merge

If episode reads fail where the front camera rolls over to a new MP4, try this metadata-only repair on a copy of **Themistoflix/ginger_back_merged** at `8604d54b1727ee017f2b97f47a716f6ed38f0690`. In this archive, the affected episode timestamps still included time from an earlier MP4. The replay uses the stored videos to check a separate replacement episode Parquet. You can run it without the original recordings or re-encoding. [Pinned source archive](https://huggingface.co/datasets/Themistoflix/ginger_back_merged/tree/8604d54b1727ee017f2b97f47a716f6ed38f0690)

To check your own LeRobot v3 archive for this pattern, use the [timestamp preflight](../lerobot-v3-timestamp-preflight/).

## Replay on a copy

1. Save the [replay kit](./lerobot-v3-rollover-replay.tar.gz) and its [SHA-256 checksum](./SHA256SUMS) in the same directory. Run `sha256sum --strict --check SHA256SUMS` there before extracting the kit. Open `REPLAY.md` from the extracted directory.
2. Use the setup and source-file instructions in `REPLAY.md`. Keep the original archive and use a clean local copy containing the 17 exact files listed in the source manifest. The pinned source download is about 1.36 GB. Point `ORIGINAL_SNAPSHOT` at that copy and `TMPDIR` at a writable directory on the same filesystem, outside the snapshot.
3. Run the Bash replay. It verifies the kit and source inventory, creates a separate `replacement.parquet` and `apply.json`, and checks indexed reads on separate patched copies. The replacement SHA-256 should be `23e6ecb8a0b4657ffee5b1721f4042fe280ef32575332e138bb9983ed31706a5`. Stop if any check fails.

The decoder test used Linux x86-64 CPU, Python 3.12.16, LeRobot 0.7.0, PyArrow 26.0.1, PyAV 15.1.0, TorchCodec 0.17.0+cpu PyTorch 2.15.0+cpu, datasets 5.2.0 and NumPy 2.2.6. FFmpeg 7.1 from the PyAV wheel was available to TorchCodec.

## What changed

The replacement changes 60 cells in the front-camera `from_timestamp` and `to_timestamp` columns for episodes 89–118. The other 16 files retained their original bytes, including every MP4.

| LeRobot 0.7.0 backend | Original reads | Reads after repair |
| --- | --- | --- |
| PyAV | 60 of 238 failed with `FrameTimestampError` | 238 of 238 matched |
| TorchCodec | 60 of 238 failed with `IndexError` | 238 of 238 matched |

The independent decoder check compared both cameras with reference frames at explicit positions in the stored videos. It covered both sides of all 118 episode joins and the two archive endpoints. The revised writer generated the same Parquet and apply receipt byte for byte. Its separate check exercised refusals and verified that a failed comparison stopped the replay. Full decoder replay of that revision was not run during those checks. The measured result covers stored frames on this one revision and rollover pattern. Capture-time synchronization remains unverified.

## Roll back

Discard the patched copies to return to the original archive. If you installed the replacement in a working copy, restore `meta/episodes/chunk-000/file-000.parquet` from the pinned revision. Its original SHA-256 is `9db02846e06c796329021c1e6113c6ace0a928718f1f8f140a611040cff92330`.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Send corrections to `hello@cybernative.ai`. We date public corrections.
