# Getting Started with MetaTrader 5 MCP Server

This MCP server provides access to the MetaTrader 5 API for trading and market data analysis through the Model Context Protocol.

## Installation

### Quick Install

```bash
git clone https://github.com/Qoyyuum/mcp-metatrader5-server
cd mcp-metatrader5-server
uv sync
```

### Configure for Claude Desktop

```bash
uv run fastmcp install src/mcp_mt5/main.py
```

Or manually add to `claude_desktop_config.json`:

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

## Basic Workflow

1. **Initialize the MT5 terminal**:
   - Use the `initialize()` tool to connect to the MT5 terminal.

2. **Log in to your trading account**:
   - Use the `login(account, password, server)` tool to log in to your trading account.

3. **Access market data**:
   - Use tools like `get_symbols()`, `copy_rates_from_pos()`, etc. to access market data.

4. **Place trades**:
   - Use the `order_send()` tool to place trades.

5. **Manage positions**:
   - Use tools like `positions_get()` to manage your open positions.

6. **Analyze trading history**:
   - Use tools like `history_orders_get()` and `history_deals_get()` to analyze your trading history.

7. **Shut down the connection**:
   - Use the `shutdown()` tool to close the connection to the MT5 terminal.

## Available Resources

The server provides helpful resources:
- `mt5://timeframes` - Available timeframe constants
- `mt5://tick_flags` - Tick flag constants
- `mt5://order_types` - Order type constants
- `mt5://order_filling_types` - Order filling type constants
- `mt5://order_time_types` - Order time type constants
- `mt5://trade_actions` - Trade action constants

## Example: Connecting to MT5 and Getting Market Data

When using with Claude Desktop or other MCP clients, you can ask the AI assistant:

> "Initialize MT5 with the default auto-detected terminal, then login with account 123456, password 'your_password', and server 'your_server'. After that, get the available symbols and show me recent price data for EURUSD on the 15-minute timeframe."

The AI will use these tools:
1. `initialize(path="")`
2. `login(login=123456, password="your_password", server="your_server")`
3. `get_symbols()`
4. `copy_rates_from_pos(symbol="EURUSD", timeframe=15, start_pos=0, count=100)`

## Example: Placing a Trade

Ask the AI assistant:

> "Place a buy order for 0.1 lots of EURUSD at market price with 20 pips deviation, stop loss at 1.0950, and take profit at 1.1050."

The AI will:
1. Get the current ask price using `get_symbol_info_tick("EURUSD")`
2. Create an order request with:
   - `action`: TRADE_ACTION_DEAL (1)
   - `symbol`: "EURUSD"
   - `volume`: 0.1
   - `type`: ORDER_TYPE_BUY (0)
   - `price`: current ask price
   - `sl`: 1.0950
   - `tp`: 1.1050
   - `deviation`: 20
   - `type_filling`: ORDER_FILLING_IOC (2)
3. Send the order using `order_send(request)`

## Important Notes

- **Always initialize MT5** before using any other tools
- **Login is required** to access account-specific data and place trades
- **Use `shutdown()`** when done to properly close the connection
- **Check order results** for success/failure before proceeding
- **Demo accounts** are recommended for testing


## Disclaimer

This software/model context protocol/author is not liable for any financial losses resulting from the use of the tools provided. Use at your own risk.
