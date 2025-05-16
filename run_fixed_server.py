#!/usr/bin/env python
"""
Fixed server runner for the MetaTrader 5 MCP server.
Uses Starlette Mount to properly wrap the FastMCP object.
"""

import os
import sys
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount

# Add the current directory to the path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the FastMCP server
from mt5_server import mcp

# Create a proper ASGI application using Starlette
app = Starlette(routes=[
    Mount("/", app=mcp)
])

if __name__ == "__main__":
    # Configure host and port
    host = os.environ.get("MT5_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MT5_MCP_PORT", "8000"))
    
    print(f"Starting MT5 MCP Server on {host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    # Run the server
    uvicorn.run(app, host=host, port=port) 