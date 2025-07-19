#!/usr/bin/env python3
"""
Simple MetaTrader 5 MCP Server - A Model Context Protocol server for MetaTrader 5.
This version uses the correct FastMCP server pattern.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mt5-mcp-server")

# Import dependencies with error handling
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    logger.info("MetaTrader5 package loaded successfully")
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 package not available")

try:
    import pandas as pd
except ImportError:
    pd = None
    logger.warning("pandas not available")
    
try:
    import numpy as np
except ImportError:
    np = None
    logger.warning("numpy not available")

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Create the MCP server
mcp = FastMCP("MetaTrader 5 MCP Server")

# Simple models for responses
class SimpleResponse(BaseModel):
    """Simple response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Initialize MetaTrader 5 connection
@mcp.tool()
def initialize() -> Dict[str, Any]:
    """
    Initialize the MetaTrader 5 terminal.
    
    Returns:
        Dict with success status and message.
    """
    if not MT5_AVAILABLE:
        logger.error("MetaTrader5 package is not available")
        return {
            "success": False,
            "message": "MetaTrader5 package is not installed or available",
            "error": "MT5_NOT_AVAILABLE"
        }
    
    try:
        if not mt5.initialize():
            error_code = mt5.last_error()
            logger.error(f"MT5 initialization failed, error code: {error_code}")
            return {
                "success": False,
                "message": f"MT5 initialization failed with error code: {error_code}",
                "error_code": error_code
            }
        
        logger.info("MT5 initialized successfully")
        return {
            "success": True,
            "message": "MT5 initialized successfully"
        }
    except Exception as e:
        logger.error(f"Exception during MT5 initialization: {e}")
        return {
            "success": False,
            "message": f"MT5 initialization exception: {str(e)}",
            "error": str(e)
        }

# Get version information
@mcp.tool()
def get_version() -> Dict[str, Any]:
    """
    Get the MetaTrader 5 version.
    
    Returns:
        Dict with version information.
    """
    if not MT5_AVAILABLE:
        return {
            "success": False,
            "message": "MetaTrader5 package is not available",
            "error": "MT5_NOT_AVAILABLE"
        }
    
    try:
        version = mt5.version()
        if version is None:
            error_code = mt5.last_error()
            logger.error(f"Failed to get version, error code: {error_code}")
            return {
                "success": False,
                "message": f"Failed to get version, error code: {error_code}",
                "error_code": error_code
            }
        
        return {
            "success": True,
            "message": "Version retrieved successfully",
            "data": {
                "version": version[0],
                "build": version[1],
                "date": version[2]
            }
        }
    except Exception as e:
        logger.error(f"Exception getting version: {e}")
        return {
            "success": False,
            "message": f"Exception getting version: {str(e)}",
            "error": str(e)
        }

# Get terminal information
@mcp.tool()
def get_terminal_info() -> Dict[str, Any]:
    """
    Get information about the MetaTrader 5 terminal.
    
    Returns:
        Dict with terminal information.
    """
    if not MT5_AVAILABLE:
        return {
            "success": False,
            "message": "MetaTrader5 package is not available",
            "error": "MT5_NOT_AVAILABLE"
        }
    
    try:
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            error_code = mt5.last_error()
            logger.error(f"Failed to get terminal info, error code: {error_code}")
            return {
                "success": False,
                "message": f"Failed to get terminal info, error code: {error_code}",
                "error_code": error_code
            }
        
        # Convert named tuple to dictionary
        terminal_dict = terminal_info._asdict()
        return {
            "success": True,
            "message": "Terminal info retrieved successfully",
            "data": terminal_dict
        }
    except Exception as e:
        logger.error(f"Exception getting terminal info: {e}")
        return {
            "success": False,
            "message": f"Exception getting terminal info: {str(e)}",
            "error": str(e)
        }

# Shutdown MetaTrader 5 connection
@mcp.tool()
def shutdown() -> Dict[str, Any]:
    """
    Shut down the connection to the MetaTrader 5 terminal.
    
    Returns:
        Dict with shutdown status.
    """
    if not MT5_AVAILABLE:
        return {
            "success": True,
            "message": "MetaTrader5 package not available - nothing to shutdown"
        }
    
    try:
        mt5.shutdown()
        logger.info("MT5 connection shut down")
        return {
            "success": True,
            "message": "MT5 connection shut down successfully"
        }
    except Exception as e:
        logger.error(f"Exception during MT5 shutdown: {e}")
        return {
            "success": False,
            "message": f"Exception during shutdown: {str(e)}",
            "error": str(e)
        }

# Test tool to verify server is working
@mcp.tool()
def test_server() -> Dict[str, Any]:
    """
    Test tool to verify the server is working.
    
    Returns:
        Dict with server status.
    """
    return {
        "success": True,
        "message": "Server is working correctly",
        "data": {
            "mt5_available": MT5_AVAILABLE,
            "pandas_available": pd is not None,
            "numpy_available": np is not None,
            "server_name": "MetaTrader 5 MCP Server",
            "version": "1.0.0"
        }
    }

# Run the server
if __name__ == "__main__":
    # Get configuration from environment or use defaults
    port = int(os.environ.get("MT5_MCP_PORT", 8000))
    host = os.environ.get("MT5_MCP_HOST", "0.0.0.0")
    
    logger.info(f"Starting MetaTrader 5 MCP server at {host}:{port}")
    logger.info(f"MT5 Available: {MT5_AVAILABLE}")
    
    # Use uvicorn to serve the FastMCP server over HTTP
    try:
        import uvicorn
        uvicorn.run(mcp, host=host, port=port)
    except ImportError:
        logger.error("uvicorn is required for HTTP transport. Install it with: pip install uvicorn")
        raise