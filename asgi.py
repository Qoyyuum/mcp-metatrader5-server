"""
MetaTrader 5 MCP ASGI Server

This module provides an ASGI-compatible server for the MetaTrader 5 MCP implementation,
allowing integration with ASGI frameworks like FastAPI, Starlette, or direct deployment
with ASGI servers like Uvicorn or Hypercorn.
"""

import logging
import os
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

# Import the MCP instance from the main module
from mt5_server import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mt5-mcp-asgi-server")

# Create a Starlette ASGI app using the preferred Streamable HTTP transport
mcp_app = mcp.streamable_http_app(path="/mcp")

# Create a FastAPI app
app = FastAPI(
    title="MetaTrader 5 MCP API",
    description="API for interacting with MetaTrader 5 via Model Context Protocol",
    version="0.1.0",
    lifespan=mcp_app.router.lifespan_context,  # Required for proper initialization
)

# Mount the MCP app
app.mount("/mt5", mcp_app)

# Add a health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    return {"status": "healthy", "service": "mt5-mcp-server"}

# Add a root endpoint for basic information
@app.get("/")
async def root() -> dict:
    """Root endpoint providing basic server information"""
    return {
        "service": "MetaTrader 5 MCP Server",
        "version": "0.1.0",
        "docs": "/docs",
        "mcp_endpoint": "/mt5/mcp"
    }

# Create a standalone app that can be used with any ASGI server
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