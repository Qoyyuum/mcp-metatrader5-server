"""
MetaTrader 5 MCP ASGI Server

This module provides an ASGI-compatible server for the MetaTrader 5 MCP implementation,
allowing integration with ASGI frameworks like FastAPI, Starlette, or direct deployment
with ASGI servers like Uvicorn or Hypercorn.
"""

import logging
import os
from fastapi import FastAPI

from mt5_server import mcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mt5-mcp-asgi-server")

http_app = mcp.streamable_http_app(path="/mcp")
sse_app = mcp.sse_app(path="/")  # Root path for SSE to maintain compatibility with existing clients

app = FastAPI(
    title="MetaTrader 5 MCP API",
    description="API for interacting with MetaTrader 5 via Model Context Protocol",
    version="0.1.0",
    lifespan=http_app.router.lifespan_context,  # Required for proper initialization
)

app.mount("/mt5", http_app)  # For Streamable HTTP transport
app.mount("/", sse_app)      # For SSE transport (at root for compatibility)

asgi_app = app

# Run the server with Uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("MT5_MCP_PORT", 8000))
    host = os.environ.get("MT5_MCP_HOST", "0.0.0.0")
    
    # Run the server
    uvicorn.run(
        "asgi:app",
        host=host,
        port=port,
        reload=os.environ.get("MT5_MCP_DEV_MODE", "false").lower() == "true"
    ) 