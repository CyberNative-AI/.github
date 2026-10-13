"""mcp-stdio-cross-era server adapter: official `mcp` 1.x SDK, README default (FastMCP + mcp.run(), stdio).

Used for mcp-1.30.0, mcp-1.28.1 and mcp-1.12.4. mcp 1.x FastMCP has no documented `version`
argument, so serverInfo.version is the SDK default (the installed mcp package version).
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("echo-server")


@mcp.tool()
def echo(message: str) -> str:
    """Echo the message"""
    return f"echo:{message}"


if __name__ == "__main__":
    mcp.run()
