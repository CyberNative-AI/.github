"""mcp-stdio-cross-era client adapter: official `mcp` 1.x Python SDK, README default (stdio_client + ClientSession).

Shared by py-mcp-1.30.0 and py-mcp-1.28.1 (impl name is taken from the installed package version).
No protocol-version, mode, timeout or compatibility option is passed to the SDK.
"""

from contextlib import AsyncExitStack
from importlib.metadata import version

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import _harness


async def run(rec, cmd, tool, args):
    params = StdioServerParameters(command=cmd[0], args=cmd[1:])
    async with AsyncExitStack() as stack:
        rec.start()
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        init = await session.initialize()
        rec.out["negotiated"] = init.protocolVersion
        rec.out["server_info"] = _harness.info_of(init.serverInfo)
        rec.done("connect", "list")

        listed = await session.list_tools()
        rec.out["tools"] = sorted(t.name for t in listed.tools)
        rec.done("list", "call")

        result = await session.call_tool(tool, arguments=args)
        rec.out["call_text"] = _harness.text_of(result.content)
        rec.out["call_is_error"] = bool(result.isError)
        rec.done("call", "close")


if __name__ == "__main__":
    raise SystemExit(_harness.main(f"py-mcp-{version('mcp')}", run))
