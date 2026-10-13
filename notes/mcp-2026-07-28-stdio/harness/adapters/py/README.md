# mcp-stdio-cross-era Python adapters

The adapters follow `../../CONTRACT.md`. Each one uses the SDK's documented default path and passes
no protocol, version, mode, timeout or compatibility option.

## Servers (`/envs/py/<venv>/bin/python /src/adapters/py/<file>`)

| venv | file | default API |
|---|---|---|
| mcp-2.3.0 | `server_mcp2.py` | `from mcp.server import MCPServer`; `MCPServer("echo-server", version="1.0.0")`; `@mcp.tool()`; `mcp.run()` |
| mcp-1.30.0, mcp-1.28.1, mcp-1.12.4 | `server_mcp1.py` | `from mcp.server.fastmcp import FastMCP`; `FastMCP("echo-server")`; `@mcp.tool()`; `mcp.run()` |
| fastmcp-4.1.0, fastmcp-3.4.8, fastmcp-2.14.0 | `server_fastmcp.py` | `from fastmcp import FastMCP`; `FastMCP("echo-server", version="1.0.0")`; `@mcp.tool`; `mcp.run()` |

mcp 1.x `FastMCP` has no `version` argument, so `serverInfo.version` is the installed mcp version
(for example `1.30.0`). This is the SDK default. The servers write nothing to stdout except protocol
traffic. The fastmcp banner and logs go to stderr.

## Clients (`/envs/py/<venv>/bin/python /src/adapters/py/<file> -- SERVER_CMD...`)

| impl | venv | file | default API |
|---|---|---|---|
| py-mcp-2.3.0 | mcp-2.3.0 | `client_mcp2.py` | `mcp.Client(StdioServerParameters(...))`, default `mode="auto"` |
| py-mcp-1.30.0 | mcp-1.30.0 | `client_mcp1.py` | `stdio_client` + `ClientSession` + `initialize()` |
| py-mcp-1.28.1 | mcp-1.28.1 | `client_mcp1.py` | same |
| py-fastmcp-4.1.0 | fastmcp-4.1.0 | `client_fastmcp.py` | `fastmcp.Client(StdioTransport(command, args))`, default `mode="auto"` |
| py-fastmcp-3.4.8 | fastmcp-3.4.8 | `client_fastmcp.py` | same (handshake-only client) |

`impl` comes from the installed package version. `_harness.py` is SDK-free and stdlib-only. It
handles argument parsing, timing, the JSON line, and a 40 s watchdog. When the watchdog fires, it
writes the JSON line and calls `os._exit(0)` without waiting for SDK teardown.

### Notes on the fastmcp client

- With the default `StdioTransport`, `keep_alive=True`, so the subprocess survives
  `async with client:`. During the close step the adapter also calls the public `client.close()`,
  which stops the subprocess inside that step.
- `call_tool` uses the default `raise_on_error=True`, so an `isError` result raises `ToolError`. The
  adapter records that as `call_ok=true, call_is_error=true` and stores the error text, the same as
  the mcp clients do for an `isError` result.
