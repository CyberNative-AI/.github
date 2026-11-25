# Check a LeRobot v3 archive's video timestamps before merging

Two command-line tools for a LeRobot v3.0 dataset on your own disk. Use them if reads fail with `FrameTimestampError` (PyAV) or `IndexError` (TorchCodec) in an archive whose cameras span more than one MP4 file, or before you merge an archive that an earlier merge produced.

- `local_preflight.py` compares each episode's stored camera timestamps with the frame index of the MP4 file it points to. It reads the archive and changes nothing.
- `local_repair.py` fixes two known patterns, described below, in a new copy of the archive. The original stays as it was.

Both are written for Python 3.12 with PyArrow and were run on Linux x86-64. Neither imports LeRobot.

## The patterns it repairs

**Rollover.** When a camera's recording continues into a new MP4 file, the stored start and end times of the later episodes should restart from that file's beginning. In this pattern they keep counting the duration of the earlier files, so they point past the end of the file they name. In our generated checks, merging such an archive with another one made LeRobot return frames from the wrong episode on some rows, without an error.

**Episodes that point at the wrong file.** When a merge started a new MP4 file partway through one source's videos, every episode of that source was given the file the merge reached at the end of the source. The earlier episodes keep their correct times but name the later file. Some of their reads fail, and others return real frames of a different episode without an error. For this pattern, the preflight works out where each episode's frames sit from the episode order, the episode lengths and each file's frame count, without the stored times. It offers this relayout only if every file is filled exactly, every stored row timestamp lands on its own episode's frame, every MP4 below `videos/` sits where `info.json` puts a camera's files, and every changed time carries one of the two offsets the kit's README describes. In our two reproductions with LeRobot 0.4.2, the relayout's file indices and times equal those of LeRobot 0.7.0's merge of the same sources in every cell.

One known cause of both is LeRobot's own merge in releases 0.4.0 to 0.4.2, fixed in pull request [#2550](https://github.com/huggingface/lerobot/pull/2550) and first released in 0.4.3. Other versions or workflows may write the same patterns.

## Use it

1. Save both files to the same directory.

   - [Download `lerobot-v3-timestamp-preflight.tar.gz`](https://raw.githubusercontent.com/CyberNative-AI/.github/94d11536780f80d1c67772e37c36b52a813be783/notes/lerobot-v3-timestamp-preflight/lerobot-v3-timestamp-preflight.tar.gz) (52 KB)
   - [Open `SHA256SUMS`](https://raw.githubusercontent.com/CyberNative-AI/.github/94d11536780f80d1c67772e37c36b52a813be783/notes/lerobot-v3-timestamp-preflight/SHA256SUMS) (SHA-256 checksum)

   If the checksum opens as text, use your browser's **Save As**. If the browser adds `.txt`, rename the saved file to `SHA256SUMS`.
   On a phone, you can also touch and hold the checksum link and choose **Download link** if available.

   Run `sha256sum --strict --check SHA256SUMS` in that directory before extracting the kit,
   then open `README.md` inside it.
2. Run the preflight on the directory that holds `meta/info.json`. It prints a JSON report with one of four results: `aligned`, `rollover_candidate` (the first pattern, with the edits listed), `relayout_candidate` (the second pattern, with the old and new file and times for each camera and episode) or `needs_review` (something else disagrees; the report says what).
3. For `rollover_candidate` or `relayout_candidate`, `local_repair.py plan` saves the proposed edits, and `copy` writes the repaired archive to a new directory only if the preflight on the copy returns `aligned`. The repair needs one episode Parquet file and regular files only. After a relayout, open a few of the listed episodes in the copy and look at the frames before you use it. To undo, delete the copy.

## Limits

- The tools check stored timestamps against each MP4's frame index. They do not decode frames or check camera sync.
- Only the two patterns above are repaired, at a constant frame rate. Every other disagreement returns `needs_review`.
- The relayout assumes the frames sit in the files in episode order. If episodes were reordered or removed after the videos were written and the frame counts still add up, it can place frames on the wrong episode and no check in the kit would notice. Two swapped episodes of the same length cannot be told apart from metadata at all. If you still have the sources, merging them again with a current release is the simpler fix.
- The kit's own checks use generated archives recorded with LeRobot 0.7.0. We reproduced the 0.4.2 merges separately. On one public archive created in November 2025, between the 0.4.0 and 0.4.3 releases, with both faults, the relayout proposed 141 camera-episode edits on two cameras. An exploratory analysis, chosen after two simpler versions had failed or been inconclusive, supports the new layout for each camera in aggregate, not episode by episode. Other LeRobot versions were not tested.

A worked example on a public archive: [LeRobot v3 episode-boundary timestamp errors after a merge](../lerobot-v3-rollover-repair/).

The code is available under the Apache License 2.0.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Send corrections to `hello@cybernative.ai`. We date public corrections.
