# Reproduce: `/home/vsts` lines in the old and the Ubuntu 26.04 agent layout

`run.sh` starts one container per image and layout and runs `shapes.sh` in it as uid 1001 with
a read-only root filesystem, writable tmpfs mounts only, and no network:

- **old layout:** `HOME=/home/vsts`, the user owns `/home/vsts`;
- **new layout:** `HOME=/home/runner`, the user owns `/home/runner`, and `/home/vsts` does not
  exist (`/home` belongs to root, as on a stock Ubuntu install).

`PATH` includes `$HOME/.local/bin`, as the hosted image's `/etc/environment` does. Images are
pinned by digest: Ubuntu 26.04, `python:3.13-slim` (3.13.16) and `node:24` (24.21.0). The uv
shape uses the uv binary you pass in; we used uv 0.10.7.

```sh
UV="$(command -v uv)" bash run.sh        # one repeat; prints one JSON line per shape
```

Each line has `layout` (`old`/`new`), `shape`, the command's exit code `rc`, `effect` and the
first error line `err`. For S4 and S6 to S8b and their `$HOME` versions, `effect` says whether the
folder or install exists afterwards; for the other shapes it is always `true`, and `rc` is the
result.

| Shape | Line under test |
|---|---|
| S1 | `cd /home/vsts/work/1/s` |
| S2 | `export PATH=/home/vsts/.local/bin:$PATH`, then call the tool by name |
| S3 | `/home/vsts/.local/bin/mytool` |
| S4 | `mkdir -p /home/vsts/.cache/x` |
| S5 | `ls /home/vsts/work/1/s` |
| S6 | `PIP_CACHE_DIR=/home/vsts/.cache/pip pip install` (offline, bundled wheel) |
| S7 | `UV_CACHE_DIR=/home/vsts/.cache/uv`, `uv venv` + `uv pip install` (offline) |
| S8 | `npm_config_cache=/home/vsts/.npm npm install` of a `file:` folder dependency |
| S8b | `npm_config_cache=/home/vsts/.npm npm install` of a local package tarball |
| S9 | `test -d /home/vsts/work` (control: reports, never fails) |
| F1, F3, F4, F6, F7, F8, F8b | the same line with `$HOME` instead of `/home/vsts` |

S8 passes in both layouts because a folder dependency never touches the npm cache; S8b is the
cache test.

[`output/run-2026-10-23.jsonl`](output/run-2026-10-23.jsonl) is the output of this script on
October 23, 2026 (Linux x86-64, Docker). Earlier runs of the same shapes that day gave the same
exit codes.
