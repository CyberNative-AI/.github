# Edits from the frozen files

This bundle was copied from the working directory and then edited only to remove internal identifiers and host paths,
and to append one dated clarification to `PROTOCOL.md` after review (the frozen entries above it are unchanged).
`FREEZE.sha256` lists the hashes of the original frozen files; the files changed here therefore no longer match it.
Each change below is the complete list for that file. Data and output files are unchanged.

| File | Original sha256 | Published sha256 | Change |
|---|---|---|---|
| `PROTOCOL.md` | `6d295ab457bc0d9299c274482046ab19677ee1e4b4e9aa40dec57eacbf1d58bd` | `ff4b61fc7cf67de4d5f538339a1d1b76696a7519dc3156001018e8fc3108c0c3` | internal study ID removed; internal owner and tracker reference removed; internal routing plan removed; host path removed; dated clarification appended: pre-freeze SPC observation marked unverified |
| `FORECAST.md` | `2bc741ea864a19c7e75fedfc3d6e71e8b51fc331ea75f2aee1c5b4055419559a` | `12a674eb67c5b1c7e1a063a91cdfd694b1981d32e42ac50b95f1d587790f2125` | internal study ID removed |
| `RESULTS.md` | `1835ba1d0e37168c88d9b6a20b2311327437736a1c2a7bc49bf32cb64c1b515c` | `3c2b23cfe4d5299c3b15620bf0e80b7a17485843e1a3f56051120c0107469967` | internal study ID removed; status points to the rerun; internal repository commit removed |
| `FREEZE.sha256` | `d7b0b49275af3712703d2ca180e4e789b61588826388a633cde665dbe14f8028` | `a8a3d754016c46e630275957356bccaa4b16dd331734e32fbb087031c406759d` | internal directory prefix removed (9 lines) |
| `src/arms.py` | `a2841d5fecee6338673ac8c7b323cb4690179301812851e6ad986db963d29ffa` | `c41b21198e621e3d2ef21dde202de5321e8a99413f780e862f2adb46eae3fa7f` | host path replaced by a relative clone path |
| `src/analyze.py` | `409b1e0e6634b1125852058fa954e7a6c9bf89c0f7f9dbe48895412bd411ed53` | `767834c4a6d53ba133553b3a17421066149b91f74edce504206e8931dbb8f01f` | internal study ID removed from docstring |
| `rerun/RERUN.md` | `51bc432bb100c7c89088afaeda5f933428e647436f4f49e90f0a7ecd3627ccd6` | `b2777a404cb6f88cd1699ecb760d208985d2193664136d7f3e4d60fe2bf32a84` | internal IDs and role name removed; internal repository commit removed; host path removed |
| `rerun/requery.py` | `c6283a515ea951993fdf714e0cc8cea00a54448253dc18e659079e7f95f8fd30` | `c0ebaf5c63f1e0dccd6070d75a271bfa38fcd7fbecbe383b6fa39e1161c1c276` | internal study ID removed from docstring |
| `rerun/descriptive_d.py` | `95969ac13fe3474eff92e80ac9efb9bd5af4837c1e2bf1933ffc5e25c27cfa1c` | `964daa9ea71ffbd11538342d831539910ba978fee2083d4a900d470fb89b9a2f` | internal study ID removed from docstring; host path replaced by a relative scratch path |
