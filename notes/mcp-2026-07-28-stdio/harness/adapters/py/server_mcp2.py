"""mcp-stdio-cross-era server adapter: official `mcp` 2.x SDK, README default (MCPServer + mcp.run(), stdio)."""

from mcp.server import MCPServer

mcp = MCPServer("echo-server", version="1.0.0")


@mcp.tool()
def echo(message: str) -> str:
    """Echo the message"""
    return f"echo:{message}"


if __name__ == "__main__":
    mcp.run()
