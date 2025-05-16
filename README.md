# MetaTrader 5 MCP Server

A Model Context Protocol (MCP) server for MetaTrader 5, allowing AI assistants to interact with the MetaTrader 5 platform for trading and market data analysis.

## Features

- Connect to MetaTrader 5 terminal
- Access market data (symbols, rates, ticks)
- Place and manage trades
- Analyze trading history
- Integrate with AI assistants through the Model Context Protocol

## Installation

### From Source

```bash
git clone https://github.com/Qoyyuum/mcp-metatrader5-server.git
cd mcp-metatrader5-server
pip install -e .
```

## Requirements

- uv
- Python 3.11 or higher
- MetaTrader 5 terminal installed
- MetaTrader 5 account (demo or real)

## Usage

### ASGI Compatibility Fix

> **Note:** This section provides alternative ways to run the server that address ASGI compatibility issues. The original methods in the main branch continue to work as intended if you don't experience these issues.

This project includes a fix for the `TypeError: 'FastMCP' object is not callable` error that may occur when running the server with Uvicorn. This is a known issue with FastMCP ([GitHub issue #69](https://github.com/jlowin/fastmcp/issues/69)) where the FastMCP objects need to be properly wrapped for ASGI compatibility.

After exploring different approaches, the simplest solution is to use FastMCP's built-in `run()` method with the SSE transport option:

```python
from mt5_server import mcp

# Configure host and port
host = "127.0.0.1"
port = 8000

# Run with SSE transport explicitly configured
mcp.run(host=host, port=port, transport="sse")
```

This creates a server with SSE (Server-Sent Events) transport, which is compatible with our LangChain MCP client. The SSE endpoint is available at the `/sse` path.

There are three ways to run the server with this fix:

#### Option 1: Using the fixed runner script (Recommended)

The simplest way to run the server:

```bash
python run_fixed_server.py
```

This will start the server on 127.0.0.1:8000 by default with the SSE endpoint at `/sse`. You can configure the host and port using environment variables:

```bash
# Windows (Command Prompt)
set MT5_MCP_HOST=0.0.0.0
set MT5_MCP_PORT=8080
python run_fixed_server.py

# Windows (PowerShell)
$env:MT5_MCP_HOST="0.0.0.0"
$env:MT5_MCP_PORT="8080"
python run_fixed_server.py

# Linux/macOS
export MT5_MCP_HOST=0.0.0.0
export MT5_MCP_PORT=8080
python run_fixed_server.py
```

#### Option 2: Native FastMCP Server

For simpler use cases, you can use FastMCP's built-in server implementation:

```bash
python run_native_server.py
```

This uses the built-in `mcp.run()` method with SSE transport, which avoids ASGI compatibility issues entirely.

#### Option 3: Development mode with main.py

By default, this will attempt to use the original Uvicorn approach, falling back to SSE transport if needed:

```bash
# Windows (Command Prompt)
set MT5_MCP_DEV_MODE=true
python main.py

# Windows (PowerShell)
$env:MT5_MCP_DEV_MODE="true"
python main.py

# Linux/macOS
export MT5_MCP_DEV_MODE=true
python main.py
```

To explicitly use SSE transport:

```bash
# Windows (Command Prompt)
set MT5_MCP_DEV_MODE=true
set MT5_MCP_USE_SSE=true
python main.py

# Windows (PowerShell)
$env:MT5_MCP_DEV_MODE="true"
$env:MT5_MCP_USE_SSE="true"
python main.py

# Linux/macOS
export MT5_MCP_DEV_MODE=true
export MT5_MCP_USE_SSE=true
python main.py
```

#### Option 4: Using the CLI

To run the server in development mode with the CLI using the original method:

```bash
python -m mcp_metatrader5_server.cli dev
```

To run with SSE transport instead:

```bash
python -m mcp_metatrader5_server.cli dev --use-sse
```

Or using uv:

```bash
uv run mt5mcp dev
```

You can specify a different host and port:

```bash
python -m mcp_metatrader5_server.cli dev --host 0.0.0.0 --port 8080
```

### Installing for Claude Desktop

To install the server for Claude Desktop:

```bash
git clone https://github.com/Qoyyuum/mcp-metatrader5-server
cd mcp-metatrader5-server
uv run fastmcp install src\mcp_metatrader5_server\server.py
```

Check your `claude_desktop_config.json` file. It should look something like this:

```json
{
  "mcpServers": {
    "MetaTrader 5 MCP Server": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "MetaTrader5",
        "--with",
        "fastmcp",
        "--with",
        "numpy",
        "--with",
        "pandas",
        "--with",
        "pydantic",
        "fastmcp",
        "run",
        "C:\\FULL_PATH_TO\\src\\mcp_metatrader5_server\\server.py"
      ]
    }
  }
}
```

## API Reference

### Connection Management

- `initialize()`: Initialize the MT5 terminal
- `login(account, password, server)`: Log in to a trading account
- `shutdown()`: Close the connection to the MT5 terminal

### Market Data Functions

- `get_symbols()`: Get all available symbols
- `get_symbols_by_group(group)`: Get symbols by group
- `get_symbol_info(symbol)`: Get information about a specific symbol
- `get_symbol_info_tick(symbol)`: Get the latest tick for a symbol
- `copy_rates_from_pos(symbol, timeframe, start_pos, count)`: Get bars from a specific position
- `copy_rates_from_date(symbol, timeframe, date_from, count)`: Get bars from a specific date
- `copy_rates_range(symbol, timeframe, date_from, date_to)`: Get bars within a date range
- `copy_ticks_from_pos(symbol, start_pos, count)`: Get ticks from a specific position
- `copy_ticks_from_date(symbol, date_from, count)`: Get ticks from a specific date
- `copy_ticks_range(symbol, date_from, date_to)`: Get ticks within a date range

### Trading Functions

- `order_send(request)`: Send an order to the trade server
- `order_check(request)`: Check if an order can be placed with the specified parameters
- `positions_get(symbol, group)`: Get open positions
- `positions_get_by_ticket(ticket)`: Get an open position by its ticket
- `orders_get(symbol, group)`: Get active orders
- `orders_get_by_ticket(ticket)`: Get an active order by its ticket
- `history_orders_get(symbol, group, ticket, position, from_date, to_date)`: Get orders from history
- `history_deals_get(symbol, group, ticket, position, from_date, to_date)`: Get deals from history

## Example Workflows

### Connecting and Getting Market Data

```python
# Initialize MT5
initialize()

# Log in to your trading account
login(account=123456, password="your_password", server="your_server")

# Get available symbols
symbols = get_symbols()

# Get recent price data for EURUSD
rates = copy_rates_from_pos(symbol="EURUSD", timeframe=15, start_pos=0, count=100)

# Shut down the connection
shutdown()
```

### Placing a Trade

```python
# Initialize and log in
initialize()
login(account=123456, password="your_password", server="your_server")

# Create an order request
request = OrderRequest(
    action=mt5.TRADE_ACTION_DEAL,
    symbol="EURUSD",
    volume=0.1,
    type=mt5.ORDER_TYPE_BUY,
    price=mt5.symbol_info_tick("EURUSD").ask,
    deviation=20,
    magic=123456,
    comment="Buy order",
    type_time=mt5.ORDER_TIME_GTC,
    type_filling=mt5.ORDER_FILLING_IOC
)

# Send the order
result = order_send(request)

# Shut down the connection
shutdown()
```

## Resources

The server provides the following resources to help AI assistants understand how to use the MetaTrader 5 API:

- `mt5://getting_started`: Basic workflow for using the MetaTrader 5 API
- `mt5://trading_guide`: Guide for placing and managing trades
- `mt5://market_data_guide`: Guide for accessing and analyzing market data
- `mt5://order_types`: Information about order types
- `mt5://order_filling_types`: Information about order filling types
- `mt5://order_time_types`: Information about order time types
- `mt5://trade_actions`: Information about trade request actions

## Prompts

The server provides the following prompts to help AI assistants interact with users:

- `connect_to_mt5(account, password, server)`: Connect to MetaTrader 5 and log in
- `analyze_market_data(symbol, timeframe)`: Analyze market data for a specific symbol
- `place_trade(symbol, order_type, volume)`: Place a trade for a specific symbol
- `manage_positions()`: Manage open positions
- `analyze_trading_history(days)`: Analyze trading history

## Development

### Project Structure

```
mcp-metatrader5-server/
├── src/
│   └── mcp_metatrader5_server/
│       ├── __init__.py
│       ├── server.py
│       ├── market_data.py
│       ├── trading.py
│       ├── main.py
│       └── cli.py
├── run.py
├── README.md
└── pyproject.toml
```

### Building the Package

To build the package:

```bash
python -m pip install build
python -m build
```

Or using uv:

```bash
uv build
```

### Publishing to PyPI

To publish the package to PyPI:

```bash
python -m pip install twine
python -m twine upload dist/*
```

Or using uv:

```bash
uv publish
```

## License

MIT

## Acknowledgements

- [MetaQuotes](https://www.metaquotes.net/) for the MetaTrader 5 platform
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server implementation
