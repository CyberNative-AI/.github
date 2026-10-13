# Protocol: MCP 2026-07-28 on stdio, cross-era SDK matrix

This is the public excerpt of the protocol we froze on 2026-10-13 before the main run. Measures, controls,
decision rule and exclusions are copied as frozen. We removed internal staff roles, task links, host paths and
budget lines, and condensed the background section. Amendments are appended below in the order they were made.
Code comments that say "frozen in PROTOCOL.md" refer to this file.

## Question

On stdio: (Q1) do the current releases' **default** clients connect, list and call tools on handshake-era
servers, as the spec promises for dual-era clients, and how long does the fallback take? (Q2) when a server
author bumps to the current release of the same SDK with default settings, which existing handshake-era clients
stop working, and what error do their users see?

Background (sources fetched 2026-10-13): the 2026-07-28 revision removes the `initialize` handshake; servers must
implement `server/discover`. The versioning page's Compatibility Matrix lists Modern × Legacy and Legacy × Modern
as failing, and Dual-era client × Legacy server as working (stdio: probe `server/discover`, fall back when it
"returns a non-modern error or times out"). The official conformance suite's `backcompat` scenarios cover auth
only, with no stdio cross-era scenario.

## Frame (fixed before any matrix run)

Implementations (adapters follow `CONTRACT.md`: documented default path, no era/mode/timeout options; source in
`adapters/`):

- Python: `mcp` 1.12.4, 1.28.1, 1.30.0, 2.3.0; `fastmcp` 2.14.0, 3.4.8, 4.1.0 (servers all 7; clients mcp
  1.28.1, 1.30.0, 2.3.0, fastmcp 3.4.8, 4.1.0).
- TypeScript: `@modelcontextprotocol/sdk` 1.29.0, 1.32.1 (server: McpServer + StdioServerTransport; client:
  Client + StdioClientTransport); v2 2.3.1 client (default `Client`) and server `serveStdio(factory)`, the stdio
  entry named by the v2 docs. Descriptive extra server `ts-v2-2.3.1-connect` (v1-style wiring kept after upgrade).
- Go: `go-sdk` v1.6.1, v1.8.0; `mcp-go` v0.57.0, v1.2.1 (servers and clients), static binaries, go1.26.9.
- Official reference servers: `server-everything` 2026.7.4 and 1.0.0, `server-filesystem` 2026.7.4 and 1.0.0.
- Synthetic spec-shaped servers `fake_server.py` (stdlib): `modern`, `dual`, `legacy_32602`, `legacy_silent`
  (no reply before initialize), `legacy_exit` (exits on a pre-initialize request).

SDK roots (for counting defects): py-mcp {mcp *}, py-fastmcp {fastmcp *}, ts {sdk 1.x, v2, reference servers},
go-sdk, mcp-go.

The era of every implementation is **measured**, not assumed:

- Servers: `probe_era.py` (stdlib, SDK-independent) gives DUAL / MODERN_ONLY / LEGACY_ONLY / NEITHER, plus the
  reply shape to a first `server/discover` (result / error code / silence 5 s / exit).
- Clients: classification run (tag `classify`) against the synthetic fixtures only, before the main matrix.
  First client-to-server method `initialize` ⇒ LEGACY; `server/discover` first and an `initialize` later against
  `legacy_32602` ⇒ DUAL; `server/discover` first and no `initialize` against `legacy_32602` ⇒ MODERN_ONLY. Labels
  are written to `client_era.json` before the main matrix starts.

Main matrix: every client × every real server (SDK adapters and reference servers), 3 repeats, seeded shuffled
order (seed 13340), hard timeout 45 s per run (client watchdog 40 s), `node:22-bookworm` containers (Python
3.11.2, Node 22), `--network none`, environments read-only.

Descriptive arm (not in the decision): every client × synthetic `legacy_32602`, `legacy_silent`, `legacy_exit`,
`dual`, `modern`, 3 repeats.

## Pilot exposure before freeze (disclosed)

The adapter authors ran each client against its own-version server; the TS clients against the four reference
servers (all completed); the Go 1.8.0 and mcp-go 1.2.1 clients against their own synthetic silent and exiting
legacy servers (go-sdk 1.8.0 hung on silence and failed on exit; mcp-go 1.2.1 fell back after 5.0 s on silence and
failed on exit); and raw probes of the Node, Go and reference servers. Source reading: the TS v2 client default is
legacy (no probe); the go-sdk 1.8.0 probe has no timeout of its own; the mcp-go 1.2.1 probe timeout is 5 s. No
cross-SDK cell of the main matrix was run. A known-issue list was frozen before the main run (GitHub issue search,
7 repositories, 6 keywords, issues created after 2026-05-01).

## Measures

- Run outcome: PASS = connect, list (contains the expected tool) and call (expected text) all succeed; else FAIL
  with stage (`TIMEOUT` if the 45 s guard fired). HARNESS = adapter printed no JSON without a timeout (excluded per
  cell). Cell verdict PASS/FAIL if ≥ 2 of 3 runs agree, else FLAKY (excluded from every count).
- Spec expectation per cell from the measured eras via the spec Compatibility Matrix (Works / Fails).
- **F items**: distinct (client implementation, server SDK root) pairs with a spec-**Works** cell that FAILs, on
  cross-era cells only (cells where client and server are both LEGACY-era are baseline, reported separately).
- **U items** (server upgrade): lines {mcp 1.30.0→2.3.0, fastmcp 3.4.8→4.1.0, ts-sdk 1.32.1→v2 2.3.1, go-sdk
  1.6.1→1.8.0, mcp-go 0.57.0→1.2.1, everything 2026.7.4→1.0.0, filesystem 2026.7.4→1.0.0} where ≥ 1 LEGACY client
  PASSes the old server and FAILs the new default server.
- **Uc items** (client upgrade): lines {mcp 1.30.0→2.3.0, fastmcp 3.4.8→4.1.0, ts-sdk 1.32.1→v2 2.3.1, go-sdk
  1.6.1→1.8.0, mcp-go 0.57.0→1.2.1} where the new default client FAILs ≥ 1 real server the old client PASSes
  (spec-permitted or not; reported with the spec label).
- D = F ∪ U ∪ Uc items; each item's responsible root = client root (F, Uc) or server root (U).
- **SLOW**: spec-Works PASS cells whose median recorder fallback gap (first `server/discover` → first
  `initialize`) ≥ 1,000 ms.
- Known vs new: each D item is matched against the frozen known-issue list (same behaviour and same SDK).
- Diagnostic quality (descriptive): for each LEGACY-client FAIL, whether `error_msg` names a protocol version
  (`20\d\d-\d\d-\d\d`) or "protocol version".

## Controls (INVALID if any fails)

- Self cells: every client PASSes 3/3 against its own package version's server.
- Probe controls: synthetic `modern` → MODERN_ONLY, `dual` → DUAL, `legacy_32602` → LEGACY_ONLY, and the `mcp`
  1.12.4 server (2025 release) → LEGACY_ONLY. SDK server eras are outcomes, not controls.
- Recorder transparency: one self cell per language (py-mcp-2.3.0, ts-v2-2.3.1, go-sdk-1.8.0) run 3× without
  `tap.py`: same outcome 3/3 and median `t_connect_ms` within ±200 ms of the tapped runs.
- Harness errors ≤ 2 % of main runs overall and ≤ 10 % for any one client.

## Decision rule (frozen)

- INVALID if a control fails.
- CONTINUE if |D| ≥ 2 spanning ≥ 2 responsible roots, and ≥ 1 D item is not described by a known issue.
- CHANGE if |D| ≥ 1 otherwise (including when every item is already known), or SLOW ≥ 1.
- STOP if |D| = 0 and SLOW = 0 (the default stdio paths keep the installed base working).

A modern-only default is permitted by the spec, so U/Uc items count practical breakage for existing users, not
spec violations; the spec label is reported per item.

## Not tested (limitations fixed in advance)

Streamable HTTP; hosts' own client code (Claude Desktop, Cursor, VS Code); Rust/Java/C#/Kotlin SDKs; non-default
options (pinned modes, custom probe timeouts); tool features beyond list/call (sampling, roots, elicitation,
subscriptions); third-party community servers.

## Freeze record

- Venvs `mcp-1.12.4` and `fastmcp-2.14.0` were resolved with `uv --exclude-newer` at each release date
  (`setup_py_dated.sh`): a plain install today gives pydantic 2.14 (mcp 1.12.4 import error) and mcp 2.3.0
  (fastmcp 2.14.0 has an unbounded `mcp>=1.23.1`; import error). The other venvs were resolved on 2026-10-13.
- Client eras (`client_era.json`, tag `classify`, fixtures only): DUAL = py-mcp-2.3.0, py-fastmcp-4.1.0,
  go-sdk-1.8.0, mcp-go-1.2.1; LEGACY = py-mcp-1.28.1, py-mcp-1.30.0, py-fastmcp-3.4.8, ts-sdk-1.29.0,
  ts-sdk-1.32.1, ts-v2-2.3.1 (the v2 TS client's default is the handshake), go-sdk-1.6.1, mcp-go-0.57.0.
- Before the freeze, an AI model critiqued protocol v1 (text only, no tools, not blind to the project). Its
  critique changed the design: client era from fixtures, synthetic positive probe controls, client-upgrade items,
  defects counted by (client, server root) on cross-era cells, roots and the known-issue requirement for CONTINUE,
  the recorder-gap SLOW measure, timing transparency and the per-client harness bound.
- Execution: `run_matrix.py` tags `main` (real servers), `descriptive` (synthetic and ts-v2-connect), `notap`
  (transparency); container limits `--cpus 2 --memory 2g --pids-limit 512`.

## Amendments (append-only)

**A01, during the main run, before any analysis.** `run_matrix.py` gained a `--notap` flag (server command passed
directly, no `tap.py`). The recorder-transparency control requires runs without the recorder, which the frozen
runner could not express. Default behaviour is unchanged. The `notap` and `descriptive` runs ran in a fourth
container concurrently with the three `main` containers, so the transparency comparison is under comparable load.

**A02, post hoc (after the frozen analysis; labelled, does not replace the frozen ruling).** The frozen rule ruled
CHANGE solely on SLOW = 8 cells (every DUAL client × fastmcp 2.14.0 / 3.4.8 servers; recorder discover→initialize
gap 1.6–2.3 s). That gap includes the legacy server's own start-up before it can answer the probe.
`posthoc_gap.py` splits it with the recorder timestamps into server reply latency and client fallback latency
(probe error reply → `initialize` sent). First run: client fallback ≤ 25.6 ms in all 52 DUAL-client × legacy-server
cells; on the same legacy servers DUAL and LEGACY clients connect in about the same time. SLOW therefore measured
server start-up, not a fallback penalty: a metric-definition defect introduced at freeze.

**A03, after the rerun (scope correction; frozen numbers unchanged).** A second run from the committed scripts
reproduced every frozen number (`results/rerun/`). It found that the frame's oldest real server, `mcp` 1.12.4,
postdates Python SDK releases that are silent on `server/discover` (1.2.1, 1.6.0, 1.8.1); 1.2.1 and 1.6.0 break all
four probing clients (supplementary runs outside the frame, `supplementary/`). The substantive reading is scoped to
the builds tested. Reproducibility documentation defects found by the rerun: Go builds are byte-identical only with
`go build -trimpath` (CGO off), which no original script recorded; `setup_py.sh` followed by `setup_py_dated.sh`
needs the two import-broken venvs moved aside by hand; starlette is unpinned (1.7.0 → 1.8.0 on rebuild, an HTTP
library not used on stdio); the internal freeze hash list was not refreshed after A01. These are recorded, not fixed
in the frozen scripts; `rerun/` holds the scripts the second run used to work around them.

**Exclusion, supplementary only.** The `fastmcp` 2.2.0 server in the supplementary setup exited for every client,
old and new, so it is an invalid fixture. Its raw failures are kept in `results/supplementary/` and it is excluded
from every compatibility statement.

## Data origin and licences

- Harness, adapters and synthetic servers: written for this experiment, MIT licence (`../LICENSE`).
- SDKs and reference servers: installed at run time from PyPI, npm and the Go module proxy under their own
  licences; none is redistributed here. Exact resolved versions are in `rerun/env-snapshot/` and the adapters'
  `go.sum` files.
- Recorded results: synthetic test traffic only (an echo tool with the strings `hello-re13340` and
  `re13340-probe`, which are opaque test markers). No personal data, no external endpoints, no credentials.
- PyPI download counts: public ClickHouse PyPI dataset; query in `../results/supplementary/PYPI-QUERY.md`.
