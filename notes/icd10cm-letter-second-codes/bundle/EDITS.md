# Edits from the study files

This folder was copied from the study's working directory and then edited for publication. The edits remove internal
identifiers, our internal routing and host details, reword contributor descriptions for a public reader, add a
rerun summary and a reproduction section, and move some files. No row, count, class or ruling was changed:
`score.json`, `patterns.json` and `check_fix.out` here are byte-identical to the study's files, and the build checks
that by recomputing them.

## Text and code

| File | Original sha256 | Published sha256 |
|---|---|---|
| `PROTOCOL.md` | `1163c3611a953215ae9af8fdda16d2891fae174180a332c36a9335b6dedec8c4` | `90b987704fbfcc0399ba7412e5abfc8bbb9bdb816c01b747b5ac7b0818839ae5` |
| `RESULTS.md` | `869babd908f63606e86a769631159fc0efe466bf512c08e3fd0ff707ebfa8051` | `841941553af51354df1ce41af3cf345b32dc2f7685253b8ec5e5510c2d52da80` |
| `adapters/node_tools.mjs` | `fdcccd6ce61f216b19eb607e4ceda20cd2422c08350c87ac3dcb313edbd8cd9e` | `ad46be1e8904f7255645e17f8c215bacba3acea5afa5ed6bfa5628e5351904d1` |
| `adapters/py_tools.py` | `d1cce40130a1ce33e861474f5b06d356add029e73c6e63a9aa1b66073e1d47aa` | `8bd8831db2591ee60000749f02c1a2c79a05edb1199c844cb795f17648e24ca1` |
| `adapters/services.py` | `9a9784ed9ee3b44e8ef9964f20b58eeae9e65de04aa9ac9b27058661c68be814` | `ca49437811314a99f748dc01da62da7febf89d995f41a4179d99b76e48b1c57b` |
| `rerun/RERUN.md` | `4da87187e9b8b2bc58f908c987b539158d2a426bd9834132a1fb2e93c913ea6b` | `794b4bddcb568bbb1f1047d5cfe6613a073186240ceaf85d7ccb8cca246bf753` |
| `src/prep.py` | `19d4630e5c8de4c8e398e83e16d105aba9b12a583eb44ee8d9c95ec23778b10e` | `d9b3bf0393f7ed2cdb68f2948a52623babc4a69f5ea6f10bd633f172002eb55c` |
| `src/score.py` | `8b3aa5c22fa4386f70ed96fb7bf9b525e4a69a9c3c584dffe4b5f0f26dc7b0ca` | `4291b4e80794acecca4f5bfb22371330f63724fe075f60fc42413ed4affbfa1f` |

- `PROTOCOL.md`: internal study ID, owner and tracker reference removed from the title and status line; the name of
  our internal job-admission tool removed (the limits it applied, 2 CPU and 4 GB, are kept); the "Consequences"
  section's internal routing replaced by neutral wording with the same meaning; "I read" changed to "we read". The
  random seed `13826` is unchanged.
- `RESULTS.md`: internal study ID removed from the title; the private commit reference replaced by a pointer to
  `FREEZE.sha256`; contributor wording made explicit ("the AI agent that designed the study"); `run2/svc` renamed
  `run2-svc` (see below). The "Files" section is replaced by the rerun summary, a file list, the reproduction
  commands and a data and license section.
  A dated correction is appended under "Deviations": the service adapter's fixed 0.5 s pause did not enforce
  the protocol's 0.5 requests/s ceiling. The full-rerun commands are labelled as a historical outline, with the
  limits they do and do not set. The data section adds the CDC non-endorsement and no-charge notice.
  In the pattern-arm finding, two unsupported phrases are removed: "most-copied" (no copy counts were measured)
  and the remark that the 2019 pattern's claim held until FY2026 (it already rejected the leading-U code `U07.1`,
  valid since April 2020). The measured pattern results are unchanged.
- `adapters/py_tools.py`, `adapters/services.py`, `adapters/node_tools.mjs`, `src/prep.py`, `src/score.py`: internal
  study ID removed from the first comment line; in `prep.py` a comment that named a local directory now points to
  `inputs/SOURCES.md`. No code changed.
- `rerun/RERUN.md`: the rerun's own notes. Internal study and tracker IDs, a private commit reference, local install
  paths and our job-admission tool's name removed; file references updated to this layout; a note on the layout and
  a correction appended (run 1 did record its full environment, now in `env/`).

`FREEZE.sha256` and `inputs/SOURCES.sha256` are copied unchanged. The `FREEZE.sha256` hashes of `PROTOCOL.md` and
the five code files above refer to the unedited copies.

## Files added after the result
- `src/check_fix.py` and `check_fix.out`: apply the two public patterns and their position-2 edits to the 88 probes.
  Written after the result for the public note.
- `src/table.py`: prints the per-tool table from `score.json`.
- `inputs/SOURCES.md`: download URLs for the CDC files, the CDC non-endorsement and no-charge notice, and the
  commands that rebuild the probes.
- `env/`: the main run's install scripts and environment record, copied from the run's work directory. The scripts
  use `/w/env`, the mount point inside the container.
- `LICENSE`: MIT, for the code.

## Files moved or renamed
- The second service pass, `run2/svc/*.jsonl` in the study folder, is in `run2-svc/` here. `score.json` was computed
  when `run2/` held only the offline tools, so this layout makes `python3 src/score.py run1 run2` reproduce it byte
  for byte. Gate G2 (identical reruns) applies to offline tools only; the services' agreement across three passes is
  reported in `RESULTS.md`.
- `run1/svc/.done_at` and `run2/svc/.done_at` are `run1/svc/done_at.txt` and `run2-svc/done_at.txt`.
- The rerun's `rows/run1`, `rows/run2` and `rows/svc` are `rerun/run1`, `rerun/run2` and `rerun/run1/svc`; its
  `inputs/SOURCES.verified.sha256` is `rerun/SOURCES.verified.sha256`. Its rebuilt `probes.jsonl` and
  `probes.meta.json` are not copied, because they are byte-identical to `inputs/`.

## Not changed
Raw rows, gate rows, probes, controls, source hashes, `score.json`, `patterns.json` and `check_fix.out` are copied
byte for byte. The `maintainer` field in `score.json` holds the public registry account or package name that the
ruling's "different maintainers" rule counts; all 11 values are distinct. Public sources cited in `PROTOCOL.md` and
`src/patterns.py` are named as published.
