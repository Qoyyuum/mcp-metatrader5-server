#!/usr/bin/env python
"""
Native server runner for the MetaTrader 5 MCP server.
Uses FastMCP's built-in run method with SSE transport.
"""

import os
import sys

# Add the current directory to the path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the FastMCP server
from mt5_server import mcp

if __name__ == "__main__":
    # Configure host and port from environment variables
    host = os.environ.get("MT5_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MT5_MCP_PORT", "8000"))
    
    print(f"Starting MT5 MCP Server on {host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    # Run the server with SSE transport
    mcp.run(host=host, port=port, transport="sse") 