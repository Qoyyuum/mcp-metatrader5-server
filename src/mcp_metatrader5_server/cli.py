"""
MetaTrader 5 MCP Server - Command Line Interface

This module provides a command-line interface for the MetaTrader 5 MCP server.
"""

import argparse
import logging
import os
import sys
import subprocess
from importlib.metadata import version
import inspect

from mcp_metatrader5_server.main import mcp

logger = logging.getLogger("mt5-mcp-server.cli")

def get_version():
    """Get the package version."""
    try:
        return version("mcp-metatrader5-server")
    except Exception:
        return "0.1.0"  # Default version if not installed

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="MetaTrader 5 MCP Server - A Model Context Protocol server for MetaTrader 5"
    )
    
    parser.add_argument(
        "--version", "-v", action="store_true", help="Show version and exit"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Dev command
    dev_parser = subparsers.add_parser("dev", help="Run the server in development mode")
    dev_parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host to bind to"
    )
    dev_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to"
    )
    dev_parser.add_argument(
        "--use-sse", action="store_true", help="Use SSE transport instead of ASGI/Uvicorn"
    )
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install the server for Claude Desktop")
    
    args = parser.parse_args()
    
    if args.version:
        print(f"mcp-metatrader5-server version {get_version()}")
        return 0
    
    if args.command == "dev":
        # Run in development mode
        os.environ["MT5_MCP_DEV_MODE"] = "true"
        
        # Check if we should use SSE transport
        if args.use_sse:
            try:
                # Run the server directly with SSE transport
                logger.info(f"Starting server at {args.host}:{args.port} with SSE transport")
                print(f"SSE endpoint available at http://{args.host}:{args.port}/sse")
                mcp.run(host=args.host, port=args.port, transport="sse", reload=True)
                return 0
            except Exception as e:
                logger.error(f"Failed to start server with SSE transport: {e}")
                return 1
        else:
            # Original approach using Uvicorn (main branch functionality preserved)
            try:
                # Use uvicorn directly
                import uvicorn
                logger.info(f"Starting server at {args.host}:{args.port} with ASGI/Uvicorn")
                uvicorn.run(
                    "mcp_metatrader5_server.main:mcp",
                    host=args.host,
                    port=args.port,
                    reload=True
                )
                return 0
            except ImportError:
                # If uvicorn is not available, try using the command line
                logger.info("Uvicorn import failed, trying command line uvicorn")
                cmd = [sys.executable, "-m", "uvicorn", "mcp_metatrader5_server.main:mcp", 
                      f"--host={args.host}", f"--port={args.port}", "--reload"]
                logger.info(f"Running command: {' '.join(cmd)}")
                return subprocess.call(cmd)
            except Exception as e:
                # If uvicorn fails, try the SSE transport as a fallback
                logger.warning(f"ASGI/Uvicorn approach failed with {e}, trying SSE transport as fallback")
                try:
                    logger.info(f"Starting server at {args.host}:{args.port} with SSE transport")
                    print(f"SSE endpoint available at http://{args.host}:{args.port}/sse")
                    mcp.run(host=args.host, port=args.port, transport="sse", reload=True)
                    return 0
                except Exception as e2:
                    logger.error(f"Failed to start server with SSE transport: {e2}")
                    return 1
    elif args.command == "install":
        # Install for Claude Desktop
        try:
            # Try the original approach first
            cmd = [sys.executable, "--with", "mcp-metatrader5-server", "fastmcp", "install", "src\\mcp_metatrader5_server\\server.py"]
            logger.info(f"Installing with command: {' '.join(cmd)}")
            result = subprocess.call(cmd)
            if result == 0:
                return 0
            
            # If that fails, try the alternative approach
            logger.warning("Original install method failed, trying alternative approach")
            import fastmcp
            fastmcp.install(mcp)
            return 0
        except ImportError:
            logger.error("Failed to install MCP server for Claude Desktop")
            return 1
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
