"""mcp-stdio-cross-era server adapter: standalone `fastmcp` package, README default (FastMCP + mcp.run(), stdio).

Used for fastmcp-4.1.0, fastmcp-3.4.8 and fastmcp-2.14.0.
"""

from fastmcp import FastMCP

mcp = FastMCP("echo-server", version="1.0.0")


@mcp.tool
def echo(message: str) -> str:
    """Echo the message"""
    return f"echo:{message}"


if __name__ == "__main__":
    mcp.run()
