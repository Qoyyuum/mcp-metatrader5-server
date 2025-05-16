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
    # Display config info
    host = "127.0.0.1"  # Default host
    port = "8000"       # Default port
    
    print(f"Starting MT5 MCP Server (default configuration is {host}:{port})")
    print(f"SSE endpoint should be available at http://localhost:8000/sse")
    print("Press Ctrl+C to stop the server")
    
    # Run using the simplest form of the run method
    mcp.run(transport="sse") 