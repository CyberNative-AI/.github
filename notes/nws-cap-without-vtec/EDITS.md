# Edits from the frozen files

This bundle was copied from the working directories and then edited to remove internal identifiers, host names and
internal routing text, to point `RESULTS.md` at the second run, and (2026-10-14, after pre-publication review) to append
dated corrections that scope the interpretation to what was measured. `FREEZE.sha256` lists the hashes of the original
frozen files; the files changed here therefore no longer match it. Each change below is the complete list for that file.
Raw alert bodies and machine outputs (`raw-snapshot.tar.xz`, `out/`, `rerun/*.out`, `rerun/fresh_counts.txt`) are unchanged.
`rerun/fresh-raw.tar.xz` was repacked: its 27 members have the same paths, modes, times and SHA-256 contents; only the
archive owner metadata changed.

| File | Original sha256 | Published sha256 | Change |
|---|---|---|---|
| `PROTOCOL.md` | `7b073eb0083a700a23b12e66d360ce233f56749100dd704a63431531d9839aa1` | `9eeecea28664b3719743f57e67ff8d759cb786be8a43dc863a5388d94ef636f8` | internal study ID removed; internal owner and tracker reference removed; internal routing plan removed (CONTINUE rule and stop/next section; thresholds unchanged) |
| `FORECAST.md` | `7992b2cb483ca170427cde19fde6189580ef731a96d0c06328a8199fa7e09acf` | `55b7259c23ca62ae365e2d64da7704673711f740142dc7024ed4ee7cbb639b0a` | internal study ID and role name removed; "blind" removed from the title; the sentence on what the forecaster saw replaced by a public limitation (the forecast was not fully blinded to prior project context, so contextual contamination cannot be excluded); forecast and pre-freeze changes unchanged |
| `RESULTS.md` | `26f503d78a5947266d6e3bfb1e74163fb41326bf5576260973d319b74f24e0fb` | `cd87e07180cfd8e5d9c791128745db648c20d5d0c2fdb696ce1b6adf76f9f684` | internal study ID removed; internal repository commit removed; status points to the rerun; internal routing clause removed; labelled historical; dated correction (2026-10-14) appended that supersedes over-broad interpretations (body otherwise kept as written) |
| `FREEZE.sha256` | `dc951d68689f8394ac0b5c9a67851ccbd65fbef7c93188a30915b1593f3541d9` | `12c600d0357eab373e67c88516cf9414d9fc4e9b94c3b460d2032d8c76c0a3ce` | internal directory prefix removed (8 lines) |
| `src/analyze.py` | `a6d3ad2d69e0715888c6ad13874aaf6c6189824984b7f96beedafd552b0a1dd8` | `a38813a370606267f7ff78d94b9a55537336e048103eaab2a4b22a504efe0b28` | internal study ID removed from docstring |
| `rerun/REPORT.md` | `da350a79218625a497dbd5a30eafe9e194077903dee92684c0d13400eb14acd1` | `28301536550dcedfa79228c06b4e252170a3a3ffe450646fda899b31426a3466` | internal study IDs removed; host name removed; internal repository commit and directory removed; conclusion sentence scoped to this grouping rule and the 913 evaluated keys; fresh-archive hash reference replaced by a pointer to this file |
| `rerun/src/fetch_fresh.py` | `b6017ebf61305ce0896b82d71e3bc46066941808195b7c3c6cb8329fe06ddb2c` | `16c2e48c2e730626de4de18c3ea0c4c15907bdf84088bac9fcb4bc996849251e` | internal study ID removed from docstring |
| `rerun/src/spot_extra.py` | `3096996941c4dd7040c35857029302d0c332090141d0b1c259ef793907524768` | `029c968ded869ccac18089f4755a1e5a4a8131c49e3968999725c7f7c27a104c` | internal directory replaced by the bundle-relative snapshot path (run from `rerun/`) |
| `rerun/fresh-raw.tar.xz` | `395e9f517a58ec92d13fd8d1e15a3542814d0e367979fa072ee51b10339c6a37` | `0e1af2e389f11a735f79012b69711502b979085cc27c42ce95e2d9caa355dc76` | repacked (ustar, xz) with uid/gid 0 and empty owner/group names; 27 members, same paths, modes, mtimes and SHA-256 contents |
