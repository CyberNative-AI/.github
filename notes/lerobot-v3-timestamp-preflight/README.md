# Check a LeRobot v3 archive's video timestamps before merging

Two command-line tools for a LeRobot v3.0 dataset on your own disk. Use them if reads fail with `FrameTimestampError` (PyAV) or `IndexError` (TorchCodec) in episodes stored after a camera's first MP4 file, or before you merge an archive that an earlier merge produced.

- `local_preflight.py` compares each episode's stored camera timestamps with the frame index of the MP4 file it points to. It reads the archive and changes nothing.
- `local_repair.py` fixes one known pattern, described below, in a new copy of the archive. The original stays as it was.

Both are written for Python 3.12 with PyArrow and were run on Linux x86-64. Neither imports LeRobot.

## The pattern it repairs

When a camera's recording continues into a new MP4 file, the stored start and end times of the later episodes should restart from that file's beginning. In this pattern they keep counting the duration of the earlier files, so they point past the end of the file they name. In our generated checks, merging such an archive with another one made LeRobot return frames from the wrong episode on some rows, without an error.

One known cause is LeRobot's own merge in releases 0.4.0 to 0.4.2, fixed in pull request [#2550](https://github.com/huggingface/lerobot/pull/2550) and first released in 0.4.3. Other versions or workflows may write the same pattern.

## Use it

1. Save the [kit](./lerobot-v3-timestamp-preflight.tar.gz) (41 KB) and its [SHA-256 checksum](./SHA256SUMS) in one directory. Run `sha256sum --strict --check SHA256SUMS` there before extracting the kit, then open `README.md` inside it.
2. Run the preflight on the directory that holds `meta/info.json`. It prints a JSON report with one of three results: `aligned`, `rollover_candidate` (the pattern above, with the edits listed) or `needs_review` (something else disagrees; the report says what).
3. For `rollover_candidate`, `local_repair.py plan` saves the proposed edits, and `copy` writes the repaired archive to a new directory only if the preflight on the copy returns `aligned`. The repair needs one episode Parquet file and regular files only. To undo, delete the copy.

## Limits

- The tools check stored timestamps against each MP4's frame index. They do not decode frames or check camera sync.
- Only the pattern above is repaired. A merge whose episodes point at the wrong MP4 file is not repaired. In our two reproductions with LeRobot 0.4.2, the preflight returned `needs_review` for it; the kit's README says what to do.
- The kit's own checks use generated archives recorded with LeRobot 0.7.0. We reproduced the 0.4.2 merges separately. On one public archive created in November 2025, between the 0.4.0 and 0.4.3 releases, the preflight returned `needs_review` with `video_sample_count` and offered no repair; its sample counts fit the wrong-file shape. Other LeRobot versions were not tested.

A worked example on a public archive: [LeRobot v3 episode-boundary timestamp errors after a merge](../lerobot-v3-rollover-repair/).

The code is available under the Apache License 2.0.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Send corrections to `hello@cybernative.ai`. We date public corrections.
