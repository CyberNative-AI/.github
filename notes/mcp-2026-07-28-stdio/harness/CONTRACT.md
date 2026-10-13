# mcp-stdio-cross-era adapter contract (stdio only)

Every adapter uses the SDK's **documented default** path (README / quickstart). Do not pass any
protocol-era, version, mode, timeout or compatibility option. If the SDK cannot do the job without
one, stop and report that instead of adding it.

## Server adapter `S`
- stdio server, name `echo-server`, version `1.0.0`.
- Exactly one tool `echo`, input `{"message": string}` (required), description `Echo the message`.
- Result: one text content item `echo:<message>`.
- Started as `<interpreter> <file>` with no args; runs until stdin closes.
- Nothing on stdout except protocol traffic.

## Client adapter `C`
- Invocation: `<client> -- SERVER_CMD [ARGS...]`. Launches SERVER_CMD through the SDK's own stdio
  client transport (the SDK spawns the process).
- Env `MCP_TOOL` (default `echo`) and `MCP_ARGS` (JSON object, default `{"message":"hello-re13340"}`).
- Steps, each timed with a monotonic clock from just before the SDK connect call:
  1. connect (SDK default; for dual-era SDKs this is whatever the default does),
  2. list tools,
  3. call `MCP_TOOL` with `MCP_ARGS`,
  4. close.
- Overall internal deadline 40 s (only as a harness guard; outer harness kills at 45 s).
- Print exactly one JSON line to **stdout** at the end (also on failure), keys:
  `impl` (e.g. `py-mcp-2.3.0`), `connect_ok`, `list_ok`, `call_ok` (bools),
  `tools` (sorted list of names or null), `call_text` (concatenated text content or null),
  `call_is_error` (bool or null), `negotiated` (protocol version / era string if the SDK exposes it, else null),
  `server_info` (server name/version if exposed, else null),
  `t_connect_ms`, `t_list_ms`, `t_call_ms` (cumulative ms from start, null if not reached),
  `error_stage` (`connect`/`list`/`call`/`close`/null), `error_type`, `error_msg` (first 500 chars).
- Exit 0 even on protocol failure (the JSON carries the outcome); nonzero only for harness bugs.

## Runtime
- Image `node:22-bookworm` (Python 3.11.2 system, Node 22), run as host UID, `--network none`.
- Python venvs: `/envs/py/<name>/bin/python`. Node prefixes: `/envs/node/<name>` (run with
  `node` and `NODE_PATH` or a file inside that prefix). Go: GOROOT `/envs/go`, binaries in `/envs/gobin`.
- Adapters live in `/src/adapters/{py,node,go}/`.
