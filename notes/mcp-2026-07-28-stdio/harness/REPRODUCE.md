# Reproduce

Two levels. The first only needs Python 3 and checks our numbers from the recorded raw data. The second
rebuilds the environments and reruns the main matrix with Docker.

## 1. Check the numbers from the recorded data

From the note's directory (`notes/mcp-2026-07-28-stdio/`):

```sh
sha256sum -c SHA256SUMS
python3 harness/analyze.py harness/CONFIG.json results/matrix > /tmp/first.json
cmp /tmp/first.json results/RESULT.json
python3 harness/posthoc_gap.py results/matrix | cmp - results/POSTHOC-gap.json
python3 harness/analyze.py harness/CONFIG.json results/rerun/merged > /tmp/rerun.json
cmp /tmp/rerun.json results/rerun/RESULT.json
python3 harness/posthoc_gap.py results/rerun/merged | cmp - results/rerun/POSTHOC-gap.json
```

All four comparisons are byte-identical (checked in `node:22-bookworm`, Python 3.11.2, `--network none`).
`results/matrix/` is the first run and `results/rerun/merged/` the second: per-run records (`cells.jsonl`), the
full stdio exchange of each run (`tap/`, pinned by `tap_sha256` in `cells.jsonl`), server probes (`probes/`) and
client eras (`client_era.json`).

## 2. Rerun the main matrix

Needs Docker on x86-64 Linux, the `node:22-bookworm` image, about 1.5 GB of disk for environments and 20 MB for
results. Network is used only in step 1 below (PyPI, npm, Go module proxy). Wall time on our machine for steps 2–4:
12 minutes.

Tools, placed in a work directory `W`:

| Tool | Get | SHA-256 |
|---|---|---|
| uv 0.10.7 | `uv-x86_64-unknown-linux-gnu.tar.gz` from the uv GitHub release `0.10.7`; put the `uv` binary at `W/envs/uv` | tarball `9ac6cee4e379a5abfca06e78a777b26b7ba1f81cb7935b97054d80d85ac00774`, binary `3b9d43bace955a409eb6f012b0932a4935534bdb54b85b9fd696cabbb15979a0` |
| Go 1.26.9 | `go1.26.9.linux-amd64.tar.gz` from go.dev/dl; unpack so that `W/envs/go/bin/go` exists | `42d158b4d8f7b61ac0a830567c940a86098fb7aac52e467a5ebec03ef5cc2f8d` |

Then:

```sh
bash harness/rerun/reproduce.sh W
```

`reproduce.sh` runs these steps; the scripts it calls are the ones the second run executed, unchanged:

1. **Environments** (networked): `rerun/setup-py-node.sh` builds the Python venvs and npm prefixes, moving the two
   import-broken venvs aside and rebuilding them with dated resolution (`setup_py_dated.sh`); `rerun/setup-go.sh`
   builds the Go adapters with `go build -trimpath`. This step downloads and runs third-party package install and
   build code.
2. **Probe and classify** (offline): `rerun/phase1.sh` probes every server with `probe_era.py` into `/out/probes/`
   (the driver creates that directory first) and classifies the clients into `/out/client_era.json`.
3. **Matrix** (offline, environments read-only): `rerun/mainrun.sh go`, `py`, `ts` and `aux`, each in its own
   container and output directory.
4. **Merge and analyse** (offline): `merge_results.py` concatenates `cells.jsonl` and copies `tap/` from the
   phase-1 and four matrix directories. It does not copy `probes/` or `client_era.json`, which `analyze.py` and
   `posthoc_gap.py` need, so the driver copies them from phase 1. Output: `W/out/merged/RESULT.json` and
   `POSTHOC-gap.json`.

Timings will differ from ours. Compare the verdicts, eras and counts with `results/rerun/RESULT.json`.

### Limits, mounts and aborts

Every container runs as your user with `--rm`, `--cpus 2 --memory 2g --pids-limit 512` (set `CPUS`, `MEM`,
`PIDS` to change all of them). Steps 2–4 also run with `--network none`; step 1 uses Docker's default network.

| Step | Containers at once | Wall-time limit per container (variable, default) | Writable host mounts |
|---|---|---|---|
| 1 Environments | 1 (two in sequence) | `SETUP_TIMEOUT`, 3600 s | `W/envs` (about 1.5 GB); `W/scratch` for the Go build |
| 2 Probe and classify | 1 | `PHASE1_TIMEOUT`, 900 s | `W/out/phase1` |
| 3 Matrix | 4 | `MATRIX_TIMEOUT`, 3600 s | `W/out/main-go`, `main-py`, `main-ts`, `aux` (one each) |
| 4 Merge and analyse | 1 | `MERGE_TIMEOUT`, 600 s | `W/out` |

During step 3 the four containers together may use up to 8 CPUs, 8 GB of memory and 2,048 processes. Inside each
container, `run_matrix.py` also stops any single client run that exceeds its own per-run limit; that is separate
from these step limits. `harness/` is mounted read-only in every step; steps 2 and 3 mount `W/envs` read-only, and step 4 does not mount it.
Each container's own filesystem (including `/tmp`) is discarded when it exits.

`W/out` must not exist when you start, so results from an earlier invocation are never overwritten or mixed in;
move it aside first. The driver labels its containers with an id for this invocation. If a step exits non-zero,
reaches its time limit, or the driver gets SIGINT or SIGTERM, the driver removes the containers of this invocation
(and no others), appends the reason to `W/out/INCOMPLETE`, leaves the output written so far in place, does not
merge, and exits non-zero. A failed matrix container does not stop the other three; the driver waits for them,
then stops before the merge. Treat any `W/out` that has an `INCOMPLETE` file as partial. Each step's start, end,
exit status and elapsed time are logged to `W/out/driver.log`.

**Our check of these instructions.** On 2026-10-13 we ran `SKIP_SETUP=1 harness/rerun/reproduce.sh` from this
bundle, on the same machine, reusing the environments the rerun had built with step 1 (step 1 itself was not
repeated). Output: `results/reader-check/`. All 216 main cells and 648 runs passed with run lists identical to the
rerun; all 72 descriptive cells, every server and client era, every probe shape and every control matched; D = 0 and
the frozen ruling is CHANGE. The SLOW measure listed 10 cells instead of 8: the same 8 plus `go-sdk` 1.8.0 ×
`mcp` 1.28.1 and `mcp-go` 1.2.1 × `mcp` 1.30.0, at 1,059 and 1,037 ms. In both, the server took that long to reply
to the probe and the client fell back in under 1 ms (`results/reader-check/POSTHOC-gap.json`). Client fallback over
all 52 pairings: at most 7.5 ms, median of per-pairing medians 0.7 ms. This is a check of the instructions, not an
independent reproduction.

That check used the first version of `reproduce.sh`, which ran the same containers with the same commands and
the same matrix limits, but had no step time limits, no limits on steps 1 and 4, and did not stop when a matrix
container failed. The current version adds those. We tested its failure, timeout, interruption and cleanup paths
with a stand-in for the `docker` command, and its container removal after a timeout with real Docker on a `sleep`
container. We have not run the full matrix again with the current version, and step 1 has never run under the
CPU, memory and process limits it now has; if step 1 runs out of memory on your machine, raise `MEM`.

### What a rebuild resolves

Package versions float within each pinned top-level package, except the two dated venvs. What the second run
resolved is in `rerun/env-snapshot/`: `uv pip freeze` per Python venv and `package-lock.json` per npm prefix
(`main/`), and the same for the supplementary servers (`supp/`; four venvs there are listed from their installed
package metadata because their setup did not write a freeze file). Go modules are pinned by each adapter's
`go.sum`. Known drift: starlette 1.7.0 in the first run, 1.8.0 in the second; it is an HTTP library and is not used
on stdio.

| Environment | Resolution cutoff |
|---|---|
| `mcp` 1.12.4, `fastmcp` 2.14.0 (main) | `uv --exclude-newer` 2025-08-08 and 2025-12-12 (`setup_py_dated.sh`) |
| other main venvs and npm prefixes | resolved at install time (2026-10-13) |
| supplementary `mcp` 1.2.1, 1.6.0 | `--exclude-newer` 2025-03-01 and 2025-04-15 (`supplementary/setup.sh`) |
| supplementary `fastmcp` 2.2.0, 2.10.6 | 2025-04-25 and 2025-07-25 (`supplementary/setup.sh`) |
| supplementary `mcp` 1.8.1, 1.9.4, 1.10.1, 1.11.0 | 2025-05-20, 2025-06-20, 2025-07-01, 2025-07-15 (`supplementary/setup2.sh`) |
| supplementary TypeScript SDK 1.7.0, 1.12.0 | resolved at install time (2026-10-13) |

These cutoffs are set near, not exactly at, each release date; the resolved versions in `env-snapshot/` are
what was tested.

## 3. Supplementary runs (older servers)

Same image and limits. Extra mounts: `harness/supplementary/` at `/supp`, a writable `/scratch` for caches, an empty directory at `/senv` for the
supplementary environments, the main environments at `/envs` (for the clients) and `harness/` at `/src`.

- `supplementary/setup.sh` and `setup2.sh` (networked) build the old servers into `/senv`.
- `supplementary/run.sh` (offline) probes the servers and runs the four probing clients against them, 3 runs each
  (tag `supp`; output `results/supplementary/out/`).
- The old-client check used `python3 /src/run_matrix.py /supp/config-supp-legacy.json /out --tag supp-legacy`
  (output `out2/`, one run per pairing). This command was not saved as a script; it is reconstructed from the
  `tag` and `argv` fields recorded in `out2/cells.jsonl`.
- `supplementary/run2.sh` (offline) probes `mcp` 1.8.1, 1.9.4, 1.10.1 and 1.11.0 (output `out3/`).

`fastmcp` 2.2.0 exited for every client, old and new, in this setup. It is an invalid fixture; its raw failures
are kept and it is excluded from the note's statements.
