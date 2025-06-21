# MetaTrader 5 MCP ASGI Server

This document describes how to use the MetaTrader 5 MCP ASGI server implementation. As of the latest version, the ASGI functionality has been consolidated into the main `mt5_server.py` file for simplified deployment and maintenance.

## Overview

The ASGI server implementation provides an alternative way to deploy the MetaTrader 5 MCP server using the ASGI (Asynchronous Server Gateway Interface) protocol. This allows for better integration with modern Python web frameworks and deployment options. The ASGI functionality is now integrated directly into the main `mt5_server.py` file, eliminating the need for a separate ASGI module.

## Running the ASGI Server

There are multiple ways to run the ASGI server:

### Direct Execution

The simplest way to run the server is to execute the `mt5_server.py` file directly:

```bash
python mt5_server.py
```

This will start a Uvicorn server on port 8000 (default) that hosts the MetaTrader 5 MCP server.

### Using Uvicorn Directly

You can also run the server using Uvicorn directly:

```bash
uvicorn mt5_server:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag enables auto-reloading when the code changes, which is useful during development.

### Integration with Other ASGI Servers

The ASGI application can be used with other ASGI servers like Hypercorn:

```bash
hypercorn mt5_server:app --bind 0.0.0.0:8000
```

## Configuration

The ASGI server can be configured using environment variables:

- `MT5_MCP_HOST`: Host to bind the server to (default: `0.0.0.0`)
- `MT5_MCP_PORT`: Port to bind the server to (default: `8000`)
- `MT5_MCP_DEV_MODE`: Whether to run in development mode with auto-reload (default: `false`)

## API Endpoints

The ASGI server provides the following endpoints:

- `/`: SSE transport MCP endpoint (for compatibility with existing clients)
- `/mt5/mcp`: Streamable HTTP transport MCP endpoint
- `/docs`: OpenAPI documentation (provided by FastAPI)
- `/redoc`: Alternative OpenAPI documentation (provided by FastAPI)

## Integration with Other Applications

The ASGI application can be integrated with other ASGI applications or frameworks like FastAPI or Starlette:

```python
# Example of integrating with another FastAPI application
from fastapi import FastAPI
from mt5_server import app as mt5_app

# Create a parent FastAPI application
parent_app = FastAPI()

# Mount the MT5 MCP app under a specific path
parent_app.mount("/trading", mt5_app)
```
