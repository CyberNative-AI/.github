# Same-day rerun (2026-10-13, separate agent)

Source under test: the committed files in this directory; frozen files verified against FREEZE.sha256 before running (all 9 OK). Limits: CPU Docker `--network none`
for every PROJ/GDAL/pyproj run; NCAT only for (b); $0; wall ~15 min. No outside contact.

| Item | Result |
|---|---|
| (a) recompute A1/A2/A3/S3 with committed `src/arms.py` + `src/analyze.py` (image osgeo/proj:9.9.0 @ sha256:7e1a7ff0…, aux @1b7e33d9) from committed `ncat_a0.jsonl` | REPRODUCED. CONTINUE, 230/230 = 100% > 5 cm; `results.json` and `arms.json` byte-identical (sha256 in recompute_hashes.txt) |
| (b) 30 new NCAT beta queries (seed 13471, 26 CONUS + 4 AK, 3.2 s apart, 20:17–20:21Z) | REPRODUCED. 30/30 VALID, echo ok, max |Δ| vs committed A0 = 0.0 deg, sigma unchanged. One SPC block changed (01107 Pickens AL: A0 "N/A", now zone AL W-011003); lat/lon unchanged |
| (c) A1 stderr | REPRODUCED. Empty for A1 and A2 (rerun and committed). A3 prints the epoch warning |
| (d) gdaltransform / pyproj | see RERUN comment; raw in descriptive_d.json |

Files: requery.py, ncat_requery.jsonl, descriptive_d.py, descriptive_d.json, recompute_hashes.txt.
Caveat: (b) re-queries the same NCAT beta within hours of the original pass; it shows no change in that window, not stability over time.
