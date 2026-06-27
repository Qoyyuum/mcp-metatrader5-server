# MetaTrader 5 MCP Server

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/qoyyuum-mcp-metatrader5-server-badge.png)](https://mseep.ai/app/qoyyuum-mcp-metatrader5-server)
[![PyPI version](https://badge.fury.io/py/mcp-metatrader5-server.svg)](https://badge.fury.io/py/mcp-metatrader5-server)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A Model Context Protocol (MCP) server for MetaTrader 5, allowing AI assistants to interact with the MetaTrader 5 platform for trading and market data analysis.

## Features

- 🔌 **Connect to MetaTrader 5 terminal** - Initialize and manage MT5 connections
- 📊 **Access market data** - Get symbols, rates, ticks, and historical data
- 💹 **Place and manage trades** - Send orders, manage positions, and track history
- 📈 **Analyze trading history** - Review past orders and deals
- 🤖 **AI Integration** - Seamlessly integrate with AI assistants through MCP

## Quick Start

### Installation

=== "From Source"

    ```bash
    git clone https://github.com/Qoyyuum/mcp-metatrader5-server.git
    cd mcp-metatrader5-server
    uv sync
    ```

=== "From PyPI (Coming Soon)"

    ```bash
    uv pip install mcp-metatrader5-server
    ```

### Running the Server

=== "Stdio Mode (Default)"

    For MCP clients like Claude Desktop:

    ```bash
    uv run mt5mcp
    ```

=== "HTTP Mode (Development)"

    Create a `.env` file:

    ```env
    MT5_MCP_TRANSPORT=http
    MT5_MCP_HOST=127.0.0.1
    MT5_MCP_PORT=8000
    ```

    Then run:

    ```bash
    uv run mt5mcp
    ```

### Claude Desktop Setup

Install for Claude Desktop:

```bash
uv run fastmcp install src/mcp_mt5/main.py
```

Or manually configure `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-metatrader5-server": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\mcp-metatrader5-server",
        "run",
        "mt5mcp"
      ]
    }
  }
}
```

## Requirements

- **uv** (recommended) or pip
- **Python 3.11 or higher**
- **MetaTrader 5 terminal** installed on Windows
- **MetaTrader 5 account** (demo or real)

## Available Tools

### Connection Management
- `initialize(path)` - Initialize the MT5 terminal
- `login(login, password, server)` - Log in to a trading account
- `shutdown()` - Close the connection to the MT5 terminal
- `get_account_info()` - Get trading account information
- `get_terminal_info()` - Get terminal information
- `get_version()` - Get MT5 version

### Market Data
- `get_symbols()` - Get all available symbols
- `get_symbols_by_group(group)` - Get symbols by group
- `get_symbol_info(symbol)` - Get symbol information
- `get_symbol_info_tick(symbol)` - Get latest tick data
- `copy_rates_from_pos()` - Get bars from position
- `copy_rates_from_date()` - Get bars from date
- `copy_rates_range()` - Get bars in date range
- `copy_ticks_from_pos()` - Get ticks from position
- `copy_ticks_from_date()` - Get ticks from date
- `copy_ticks_range()` - Get ticks in date range

### Trading
- `order_send(request)` - Send an order
- `order_check(request)` - Check order validity
- `positions_get()` - Get open positions
- `positions_get_by_ticket(ticket)` - Get position by ticket
- `close_position(ticket)` - Close an open position by ticket
- `orders_get()` - Get active orders
- `orders_get_by_ticket(ticket)` - Get order by ticket
- `history_orders_get()` - Get historical orders
- `history_deals_get()` - Get historical deals

## Resources

The server provides helpful resources for AI assistants:

- `mt5://timeframes` - Available timeframe constants
- `mt5://tick_flags` - Tick flag constants
- `mt5://order_types` - Order type constants
- `mt5://order_filling_types` - Order filling type constants
- `mt5://order_time_types` - Order time type constants
- `mt5://trade_actions` - Trade action constants

## Example Usage

Ask your AI assistant:

> "Initialize MT5, login to my account, and show me the current price of EURUSD"

> "Get the last 100 bars of GBPUSD on the 1-hour timeframe"

> "Place a buy order for 0.1 lots of EURUSD at market price"

> "Show me all my open positions"

## Next Steps

- [Getting Started Guide](getting_started.md) - Detailed setup and usage
- [Market Data Guide](market_data_guide.md) - Working with market data
- [Trading Guide](trading_guide.md) - Placing and managing trades
- [Pydantic AI Integration](pydantic_ai_integration.md) - Using with Pydantic AI framework
- [Publishing Guide](publishing.md) - Publishing to PyPI

## License

MIT License - see [LICENSE](https://github.com/Qoyyuum/mcp-metatrader5-server/blob/main/LICENSE) for details.

## Acknowledgements

- [MetaQuotes](https://www.metaquotes.net/) for the MetaTrader 5 platform
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server implementation
