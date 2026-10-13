# MCP 2026-07-28 on stdio: 216 of 216 tested SDK pairings work, but probing clients break Python `mcp` 1.2.1 and 1.6.0 servers

The 2026-07-28 revision of the Model Context Protocol removes the `initialize` handshake. A client now sends its protocol version with every request, and a server must answer `server/discover`. Since then, every main SDK has shipped a new major or minor line: Python `mcp` 2.x, `fastmcp` 4, the TypeScript v2 packages, Go `go-sdk` 1.8 and `mcp-go` 1.x. Dependabot is now opening pull requests that widen `mcp<2` to `<3`.

The spec says some pairings of old and new builds fail ([versioning, Compatibility Matrix](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)). It also says that a "dual-era" client, one that tries the new protocol first and falls back, works with an old server. The [conformance suite](https://github.com/modelcontextprotocol/conformance) (commit `c37eec8`, October 1, 2026) runs its scenarios over HTTP and has no stdio test that crosses the two eras, so we ran one.

**Short answer, for stdio, each SDK's default code path and the builds we tested:**

- **Server upgrades worked.** The current default server of each of the five SDKs answered both the new probe and the old handshake, and all eight old clients we tested connected to all five.
- **Client upgrades worked against most old servers we tried.** The four current clients that probe connected to all 13 old server builds in the main matrix (the oldest is `mcp` 1.12.4, from August 2025), and to `fastmcp` 2.10.6 and TypeScript SDK 1.7.0 and 1.12.0 servers outside it.
- **They failed against `mcp` 1.2.1 and 1.6.0 servers,** 3 runs out of 3 for each of the four clients. `mcp` 1.8.1 is silent on the probe in the same way, so we expect it to fail too, but we did not run clients against it. Other builds we did not test may behave differently.

If your stdio server pins `mcp` below 1.9, bump it before your users' clients move to probing defaults. Whatever it runs on, test it against the probing clients your users have.

## The main matrix: 216 of 216

12 SDK client builds against 18 server builds, from five SDKs plus the official reference servers, three runs each. All 648 runs connected, listed tools and called one.

- **Every current default server answered both eras.** `mcp` 2.3.0, `fastmcp` 4.1.0, TypeScript v2 `serveStdio` 2.3.1, `go-sdk` 1.8.0 and `mcp-go` 1.2.1 replied to `server/discover` and also completed an old `initialize` handshake.
- **Every current probing client fell back to the 13 old server builds in the matrix.** These are the `mcp` 2.3.0, `fastmcp` 4.1.0, `go-sdk` 1.8.0 and `mcp-go` 1.2.1 clients. Fallback time is measured from the server's error reply to the client's `initialize`, across those 52 pairings, three runs each. In the rerun the slowest fallback took 2.0 ms, and the median of the 52 per-pairing medians was 0.5 ms. The first run had one 25.6 ms outlier.
- **The TypeScript v2 client does not probe by default.** `@modelcontextprotocol/client` 2.3.1 opens with the old `initialize` handshake unless the application opts in to version negotiation, so upgrading it changes nothing on the wire.
- **The official reference servers still speak only the old protocol.** `@modelcontextprotocol/server-everything` and `server-filesystem` 1.0.0, released October 11, 2026, depend on `@modelcontextprotocol/sdk` 1.x and answer `server/discover` with "method not found". Every client in the matrix still worked with them.

A second run, with environments rebuilt from the committed scripts, reproduced every count and verdict. It then tested older builds outside the matrix, which is where the break turned up.

## The break: Python `mcp` 1.2.1 and 1.6.0

We ran a minimal echo server on older releases: six lines with the SDK's own `FastMCP` class for Python, and `McpServer` for TypeScript. Old clients here means three of the eight: `mcp` 1.30.0, TypeScript SDK 1.32.1 and `go-sdk` 1.6.1, one run each.

| Server build | Reply to a first `server/discover` | 4 probing clients, 3 runs each | 3 old clients, 1 run each |
|---|---|---|---|
| `mcp` 1.2.1, 1.6.0 | no reply; the process exits when the next message arrives | **all fail** | work |
| `mcp` 1.8.1 | no reply | not run | not run |
| `mcp` 1.9.4, 1.10.1, 1.11.0 | error −32602 | not run (same reply shape as 1.12.4, which passed) | not run |
| `fastmcp` 2.10.6 | error −32602 | all work | work |
| `@modelcontextprotocol/sdk` 1.7.0, 1.12.0 | error −32601 | all work | work |

The old Python servers do not answer the probe, but they keep running while the client waits. What happens next depends on the client:

- `mcp` 2.3.0, `fastmcp` 4.1.0 and `mcp-go` 1.2.1 give up on the probe and send `initialize` on the same pipe. The server then exits with status 1 without writing a reply; in all 18 such runs it was gone within 146 ms. Its traceback is a validation error on the earlier `server/discover` request. Users see `[-32000] Connection closed` after the 10 s probe timeout (`mcp`, `fastmcp`) or `transport closed` after 5 s (`mcp-go`).
- `go-sdk` 1.8.0 never sends `initialize`. It waits on the probe until the caller's deadline, with no error ([#1332](https://github.com/modelcontextprotocol/go-sdk/issues/1332), open). All six of its runs reached our 40 s limit.

Old clients connect to the same servers, because they never send the probe. That makes the failure easy to misread as a bug in the newer client.

In the spec's terms, these servers take the "times out" branch of the Compatibility Matrix, where a dual-era client with a legacy server "Works" when the "probe returns a non-modern error or times out". The fallback that follows fails, because it goes to the same server process, which exits when the next message arrives.

We also built `fastmcp` 2.2.0. It exited for every client, old and new, so we treat that build as a broken test setup and leave it out of these results. Its raw failures are in the bundle.

**How many such servers are still in use is unknown.** The only number we have is downloads: releases of `mcp` below 1.9 got 1.04 million of 240 million PyPI downloads (0.43 %) from September 12 to October 11, 2026, in the public PyPI per-version download table in ClickHouse (query and date check in `results/supplementary/PYPI-QUERY.md`). Downloads include CI and client installs and do not count installed servers. A server that someone configured once with a pinned `mcp` version can keep running for a long time.

## Check your own server

`probe_era.py` uses only the Python standard library. It starts your server twice, once with `server/discover` first and once with the old handshake, and prints one line:

```sh
curl -fsSLO https://raw.githubusercontent.com/CyberNative-AI/.github/main/notes/mcp-2026-07-28-stdio/probe_era.py
python3 probe_era.py probe.json -- python3 server.py
```

Real output, from builds in this note:

```text
# mcp 2.3.0: answers both eras
{"era": "DUAL", "discover_shape": "result", "discover_supported": ["2026-07-28"], "initialize_version": "2025-11-25", "legacy_tools_ok": true}
# @modelcontextprotocol/sdk 1.32.1: old server; the probing clients we tested worked with it
{"era": "LEGACY_ONLY", "discover_shape": "error:-32601", "discover_supported": [], "initialize_version": "2025-11-25", "legacy_tools_ok": true}
# mcp 1.6.0: old server; the probing clients we tested failed against it
{"era": "LEGACY_ONLY", "discover_shape": "silence", "discover_supported": [], "initialize_version": "2024-11-05", "legacy_tools_ok": true}
```

Read `discover_shape` as an observation, not a verdict. `result` or `error:<code>` means the probe got an answer, which is what the probing clients we tested needed. `silence` or `exit` is a warning sign: a silent server that keeps running still works with three of the four probing clients after their timeouts (see below), while `mcp` 1.6.0 is silent and then exits. Either way, test your server with the clients your users run. The full exchange is in `probe.json`.

The probe waits up to 5 seconds for each reply, and the first wait includes start-up. If your command downloads the server on launch (`npx -y …`, `uvx …`), run it once by hand first and stop it with Ctrl-C once it has started. On a cold cache the download can use up the wait, the probe can stop it partway, and a `silence`, `exit` or `NEITHER` reading then says nothing about the server.

## Hand-written stdio loops

The two bad shapes also show up in stdio servers that people write by hand. We tested two small synthetic servers. These are not real projects, and we did not sample real hand-written servers.

| Synthetic server, on a first `server/discover` | 4 probing clients | 8 old clients |
|---|---|---|
| **exits** | all fail to connect, 3 of 3 runs | all work |
| **stays silent and keeps running** | `go-sdk` 1.8.0 waits until the caller's deadline; `mcp-go` falls back after 5.0 s; `mcp` and `fastmcp` after 10.0 s | all work |

For an exiting server, the clients report `client is closing: EOF` (`go-sdk`), `transport closed` (`mcp-go`) and `[-32000] Connection closed` (Python `mcp` and `fastmcp`). For `go-sdk` the exit shape is also an open issue, [#1177](https://github.com/modelcontextprotocol/go-sdk/issues/1177).

If you wrote your own loop, answer an unknown method with a JSON-RPC error (−32601, "Method not found") and keep reading.

## About the frozen decision rule

We fixed the analysis rule before the main run (`harness/PROTOCOL.md`, with its amendments). It ruled CHANGE rather than "no problem" because of one metric. In 8 pairings, each a probing client against an old `fastmcp` server (2.14.0 or 3.4.8), the time from the probe to the client's `initialize` was 1.6–2.3 s. After the frozen analysis we split that time using the recorded message timestamps, and labelled the split as post hoc. Almost all of it is the old `fastmcp` server starting up before it can answer anything. Old clients take about as long to connect to the same servers: for `fastmcp` 3.4.8, 1,955 ms for probing clients and 1,851 ms for old ones in the first run, and 1,836 ms and 1,785 ms in the rerun. The rerun reproduced the same 8 pairings. A third run, which we made to check the rerun instructions, flagged 10: the same 8 plus two pairings with old `mcp` servers (1.28.1, 1.30.0) whose start-up crossed 1,000 ms by under 60 ms, while the client fell back in under 1 ms. The frozen ruling stands as recorded; the reading above is the post-hoc one.

The older Python builds above were added after both runs, outside the frozen design.

## What was tested

| Role | Probing (new protocol first, then fallback) | Old handshake only | New and old |
|---|---|---|---|
| Clients (12) | `mcp` 2.3.0, `fastmcp` 4.1.0, `go-sdk` 1.8.0, `mcp-go` 1.2.1 | `mcp` 1.28.1, 1.30.0; `fastmcp` 3.4.8; `@modelcontextprotocol/sdk` 1.29.0, 1.32.1; `@modelcontextprotocol/client` 2.3.1; `go-sdk` 1.6.1; `mcp-go` 0.57.0 | — |
| Servers (18) | — | `mcp` 1.12.4, 1.28.1, 1.30.0; `fastmcp` 2.14.0, 3.4.8; `@modelcontextprotocol/sdk` 1.29.0, 1.32.1; `go-sdk` 1.6.1; `mcp-go` 0.57.0; `server-everything` and `server-filesystem` 2026.7.4 and 1.0.0 | `mcp` 2.3.0, `fastmcp` 4.1.0, TypeScript v2 `serveStdio` 2.3.1, `go-sdk` 1.8.0, `mcp-go` 1.2.1 |
| Servers outside the matrix | — | `mcp` 1.2.1, 1.6.0, 1.8.1, 1.9.4, 1.10.1, 1.11.0; `fastmcp` 2.10.6; `@modelcontextprotocol/sdk` 1.7.0, 1.12.0 | — |

- Each client's era was measured from what it sends first, not from its version number. Each server's era was measured with `probe_era.py`.
- Each run connects, lists tools and calls one tool. It passes only if the tool's reply contains the expected text. Small adapter programs drive each SDK through its documented default stdio path, with no era, mode or timeout options. They are in `harness/adapters/`.
- Runs used Docker CPU containers with no network, 2 CPUs, 2 GB of memory and 512 processes each, on one machine. Every run's full stdio exchange is recorded in `results/`.
- A second AI agent reran the matrix from the committed scripts on the same machine, with every environment rebuilt from scratch. It reproduced every run outcome. This is a rerun, not an independent reproduction on other hardware.

## How to rerun

`harness/REPRODUCE.md` has the details. In short:

- **Check our numbers** with Python 3 only: `sha256sum -c SHA256SUMS`, then `harness/analyze.py` and `harness/posthoc_gap.py` on `results/matrix/` (first run) and `results/rerun/merged/` (rerun). Both reproduce the shipped `RESULT.json` and `POSTHOC-gap.json` byte for byte.
- **Rerun the matrix** with Docker: put uv 0.10.7 and Go 1.26.9 in a work directory (download names and checksums in `REPRODUCE.md`), then run `bash harness/rerun/reproduce.sh WORKDIR`. It builds the environments (the only step that needs network), probes the servers, runs the matrix offline in four containers, merges and analyses. The scripts it calls are the ones the rerun executed. We checked an earlier version of this driver once on our machine, reusing the rerun's environments: every verdict and era and the main cell and run counts matched (`results/reader-check/`). The current version adds step time limits, resource limits on every step and a stop before the merge if any container fails; `REPRODUCE.md` says what was tested.

Some notes from rebuilding the environments:

- A plain `pip install fastmcp==2.14.0` today resolves `mcp` 2.3.0 and fails on import.
- `mcp==1.12.4` resolves pydantic 2.14.1 and also fails on import.
- The setup moves those two aside and rebuilds both with `uv pip install --exclude-newer` set near each release date. The dependency versions each environment actually resolved are in `harness/rerun/env-snapshot/`.
- Go binaries match ours byte for byte only when built with `-trimpath`.

The older Python servers outside the matrix use `harness/supplementary/`; `REPRODUCE.md` lists their commands and resolution dates.

## Limits

- stdio only. Streamable HTTP was not tested.
- SDK defaults, driven by our adapters. Host applications such as Claude Desktop, Cursor or VS Code have their own client code and were not tested. Neither was the TypeScript v2 client's opt-in `auto` negotiation mode.
- Five SDKs: Python `mcp`, `fastmcp`, TypeScript, `go-sdk`, `mcp-go`. Not Rust, Java, C#, Kotlin or Swift.
- Tools list and call only, with one trivial echo tool. No resources, prompts, sampling or auth.
- One machine, three runs per pairing. The old-client checks against the older servers used three old clients, one run each.
- The server builds are a sample of releases, not a measure of what is installed. A build we did not test may behave differently from its neighbours.

Published by CyberNative AI LLC, which is responsible for this note. AI agents designed and ran the tests, analysed the results and wrote the text. Corrections: hello@cybernative.ai. We will list any correction below with its date.
