"""mcp-stdio-cross-era client adapter: official `mcp` 2.x Python SDK, documented default `mcp.Client`.

`Client(StdioServerParameters(...))` launches the server as a stdio subprocess; connect uses the
SDK default (`mode="auto"`). No protocol-version, mode, timeout or compatibility option is passed.
"""

from contextlib import AsyncExitStack
from importlib.metadata import version

from mcp import Client, StdioServerParameters

import _harness


async def run(rec, cmd, tool, args):
    client = Client(StdioServerParameters(command=cmd[0], args=cmd[1:]))
    async with AsyncExitStack() as stack:
        rec.start()
        await stack.enter_async_context(client)
        rec.out["negotiated"] = client.protocol_version
        rec.out["server_info"] = _harness.info_of(client.server_info)
        rec.done("connect", "list")

        listed = await client.list_tools()
        rec.out["tools"] = sorted(t.name for t in listed.tools)
        rec.done("list", "call")

        result = await client.call_tool(tool, args)
        rec.out["call_text"] = _harness.text_of(result.content)
        rec.out["call_is_error"] = bool(result.is_error)
        rec.done("call", "close")


if __name__ == "__main__":
    raise SystemExit(_harness.main(f"py-mcp-{version('mcp')}", run))
