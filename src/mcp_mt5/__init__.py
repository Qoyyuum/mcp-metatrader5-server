"""MetaTrader 5 MCP Server"""

from .main import mcp

__version__ = "0.1.8"
__all__ = ["main", "mcp"]


def main():
    """Entry point for the MCP server CLI"""
    import os

    from dotenv import load_dotenv

    # Load environment variables from .env file if it exists
    load_dotenv()

    # Determine transport mode from environment or default to stdio
    transport = os.getenv("MT5_MCP_TRANSPORT", "stdio")

    if transport == "http":
        host = os.getenv("MT5_MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MT5_MCP_PORT", "8000"))
        mcp.run(transport="http", host=host, port=port)
    else:
        # Default to stdio for MCP clients like Claude Desktop
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
