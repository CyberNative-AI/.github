"""mcp-stdio-cross-era client adapter: standalone `fastmcp` package, documented default `fastmcp.Client`.

Shared by py-fastmcp-4.1.0 and py-fastmcp-3.4.8. The client is given a `StdioTransport` for the
server command (fastmcp's documented transport for an arbitrary stdio command); everything else is
the default (4.x: `mode="auto"`). `async with client:` is the documented lifecycle; because the
default StdioTransport keeps the subprocess alive after the context exits (keep_alive=True), the
close step also calls the public `client.close()` so the subprocess is shut down inside the step.
`call_tool` (default raise_on_error=True) raises ToolError for an isError result; that is recorded
as call_ok=true, call_is_error=true with the error text, i.e. the call round-trip completed.
No protocol-version, mode, timeout or compatibility option is passed.
"""

from contextlib import AsyncExitStack
from importlib.metadata import version

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from fastmcp.exceptions import ToolError

import _harness


def _negotiated(client):
    pv = getattr(client, "protocol_version", None)  # 4.x era-neutral property
    if pv is None and getattr(client, "initialize_result", None) is not None:
        pv = client.initialize_result.protocolVersion
    return pv


def _server_info(client):
    if hasattr(client, "server_info"):  # 4.x era-neutral property
        return _harness.info_of(client.server_info)
    init = getattr(client, "initialize_result", None)
    return _harness.info_of(init.serverInfo) if init is not None else None


async def run(rec, cmd, tool, args):
    client = Client(StdioTransport(command=cmd[0], args=cmd[1:]))
    async with AsyncExitStack() as stack:
        stack.push_async_callback(client.close)
        rec.start()
        await stack.enter_async_context(client)
        rec.out["negotiated"] = _negotiated(client)
        rec.out["server_info"] = _server_info(client)
        rec.done("connect", "list")

        tools = await client.list_tools()
        rec.out["tools"] = sorted(t.name for t in tools)
        rec.done("list", "call")

        try:
            result = await client.call_tool(tool, args)
        except ToolError as e:
            rec.out["call_text"] = str(e)
            rec.out["call_is_error"] = True
        else:
            rec.out["call_text"] = _harness.text_of(result.content)
            rec.out["call_is_error"] = bool(result.is_error)
        rec.done("call", "close")


if __name__ == "__main__":
    raise SystemExit(_harness.main(f"py-fastmcp-{version('fastmcp')}", run))
