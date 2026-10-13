from mcp.server.fastmcp import FastMCP
mcp = FastMCP("echo-server")
@mcp.tool()
def echo(message: str) -> str:
    """Echo the message"""
    return f"echo:{message}"
if __name__ == "__main__":
    mcp.run()
