#!/usr/bin/env python3
"""
Simple launcher for the MetaTrader 5 MCP Server.
This script bypasses dependency installation issues by running directly.
"""

import sys
import os
import subprocess

def main():
    """Start the server using uvicorn directly."""
    
    # Try the CLI first
    try:
        print("🚀 Starting MT5 MCP Server using CLI...")
        result = subprocess.run([
            sys.executable, "-m", "mcp_metatrader5_server.cli", "dev",
            "--host", "0.0.0.0", "--port", "8000"
        ], cwd=os.path.dirname(__file__))
        return result.returncode
    except Exception as e:
        print(f"CLI failed: {e}")
    
    # Fallback to uvicorn
    try:
        print("🚀 Starting MT5 MCP Server using uvicorn...")
        result = subprocess.run([
            sys.executable, "-m", "uvicorn", "mt5_server:mcp",
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], cwd=os.path.dirname(__file__))
        return result.returncode
    except Exception as e:
        print(f"Uvicorn failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 