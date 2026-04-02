# API Reference

Complete reference for all tools, resources, and models provided by the MetaTrader 5 MCP Server.

## Connection Management Tools

### `initialize(path: str) -> bool`

Initialize the MetaTrader 5 terminal.

**Parameters:**
- `path` (str): Full path to the MT5 terminal executable

**Returns:**
- `bool`: True if initialization was successful, False otherwise

**Example:**
```python
initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe")
```

---

### `login(login: int, password: str, server: str) -> bool`

Log in to a MetaTrader 5 trading account.

**Parameters:**
- `login` (int): Trading account number
- `password` (str): Trading account password
- `server` (str): Trading server name

**Returns:**
- `bool`: True if login was successful, False otherwise

**Example:**
```python
login(login=123456, password="your_password", server="YourBroker-Demo")
```

---

### `shutdown() -> bool`

Shut down the connection to the MetaTrader 5 terminal.

**Returns:**
- `bool`: True if shutdown was successful

---

### `get_account_info() -> AccountInfo`

Get information about the current trading account.

**Returns:**
- `AccountInfo`: Account information including balance, equity, margin, etc.

**AccountInfo Model:**
```python
{
    "login": int,
    "balance": float,
    "equity": float,
    "margin": float,
    "margin_free": float,
    "margin_level": float,
    "profit": float,
    "currency": str,
    "leverage": int,
    "name": str,
    "server": str,
    # ... and more fields
}
```

---

### `get_terminal_info() -> Dict[str, Any]`

Get information about the MetaTrader 5 terminal.

**Returns:**
- `Dict[str, Any]`: Terminal information

---

### `get_version() -> Dict[str, Any]`

Get the MetaTrader 5 version.

**Returns:**
```python
{
    "version": int,
    "build": int,
    "date": str
}
```

---

## Market Data Tools

### `get_symbols() -> List[str]`

Get all available symbols (financial instruments).

**Returns:**
- `List[str]`: List of symbol names

---

### `get_symbols_by_group(group: str) -> List[str]`

Get symbols that match a specific group or pattern.

**Parameters:**
- `group` (str): Filter pattern (e.g., "*", "EUR*", "*.US")

**Returns:**
- `List[str]`: List of matching symbol names

---

### `get_symbol_info(symbol: str) -> SymbolInfo`

Get detailed information about a specific symbol.

**Parameters:**
- `symbol` (str): Symbol name (e.g., "EURUSD")

**Returns:**
- `SymbolInfo`: Detailed symbol information

---

### `get_symbol_info_tick(symbol: str) -> Dict[str, Any]`

Get the latest tick data for a symbol.

**Parameters:**
- `symbol` (str): Symbol name

**Returns:**
```python
{
    "time": int,
    "bid": float,
    "ask": float,
    "last": float,
    "volume": float,
    # ... more fields
}
```

---

### `copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int) -> List[Dict[str, Any]]`

Get bars from a specified position.

**Parameters:**
- `symbol` (str): Symbol name
- `timeframe` (int): Timeframe constant (1=M1, 5=M5, 15=M15, 60=H1, 240=H4, 1440=D1, etc.)
- `start_pos` (int): Initial position (0 = most recent bar)
- `count` (int): Number of bars to retrieve

**Returns:**
- `List[Dict]`: List of bars with OHLCV data

**Example:**
```python
# Get last 100 bars of EURUSD on 15-minute timeframe
rates = copy_rates_from_pos("EURUSD", 15, 0, 100)
```

---

### `copy_rates_from_date(symbol: str, timeframe: int, date_from: datetime, count: int) -> List[Dict[str, Any]]`

Get bars starting from a specific date.

**Parameters:**
- `symbol` (str): Symbol name
- `timeframe` (int): Timeframe constant
- `date_from` (datetime): Start date
- `count` (int): Number of bars to retrieve

**Returns:**
- `List[Dict]`: List of bars with OHLCV data

---

### `copy_rates_range(symbol: str, timeframe: int, date_from: datetime, date_to: datetime) -> List[Dict[str, Any]]`

Get bars within a date range.

**Parameters:**
- `symbol` (str): Symbol name
- `timeframe` (int): Timeframe constant
- `date_from` (datetime): Start date
- `date_to` (datetime): End date

**Returns:**
- `List[Dict]`: List of bars with OHLCV data

---

## Trading Tools

### `order_send(request: OrderRequest) -> OrderResult`

Send an order to the trade server.

**Parameters:**
- `request` (OrderRequest): Order parameters

**OrderRequest Model:**
```python
{
    "action": int,        # TRADE_ACTION_DEAL (0) for market orders
    "symbol": str,        # Symbol name
    "volume": float,      # Lot size
    "type": int,          # ORDER_TYPE_BUY (0) or ORDER_TYPE_SELL (1)
    "price": float,       # Order price
    "sl": float,          # Stop loss (optional)
    "tp": float,          # Take profit (optional)
    "deviation": int,     # Max price deviation in points (optional)
    "magic": int,         # Magic number (optional)
    "comment": str,       # Order comment (optional)
    "type_time": int,     # Order time type (optional)
    "type_filling": int   # Order filling type (optional)
}
```

**Returns:**
- `OrderResult`: Order execution result

**Example:**
```python
request = {
    "action": 0,  # TRADE_ACTION_DEAL
    "symbol": "EURUSD",
    "volume": 0.1,
    "type": 0,  # ORDER_TYPE_BUY
    "price": 1.1000,
    "sl": 1.0950,
    "tp": 1.1050,
    "deviation": 20,
    "type_filling": 2  # ORDER_FILLING_IOC
}
result = order_send(request)
```

---

### `order_check(request: OrderRequest) -> Dict[str, Any]`

Check if an order can be placed with the specified parameters.

**Parameters:**
- `request` (OrderRequest): Order parameters to check

**Returns:**
- `Dict[str, Any]`: Check result with validation information

---

### `positions_get(symbol: Optional[str] = None, group: Optional[str] = None) -> List[Position]`

Get open positions.

**Parameters:**
- `symbol` (str, optional): Filter by symbol
- `group` (str, optional): Filter by group pattern

**Returns:**
- `List[Position]`: List of open positions

---

### `positions_get_by_ticket(ticket: int) -> Optional[Position]`

Get an open position by its ticket number.

**Parameters:**
- `ticket` (int): Position ticket

**Returns:**
- `Position` or `None`: Position information

---

### `orders_get(symbol: Optional[str] = None, group: Optional[str] = None) -> List[Dict[str, Any]]`

Get active pending orders.

**Parameters:**
- `symbol` (str, optional): Filter by symbol
- `group` (str, optional): Filter by group pattern

**Returns:**
- `List[Dict]`: List of active orders

---

### `history_orders_get(...) -> List[HistoryOrder]`

Get orders from history within a specified date range.

**Parameters:**
- `symbol` (str, optional): Filter by symbol
- `group` (str, optional): Filter by group
- `ticket` (int, optional): Filter by ticket
- `position` (int, optional): Filter by position ticket
- `from_date` (datetime, optional): Start date
- `to_date` (datetime, optional): End date

**Returns:**
- `List[HistoryOrder]`: List of historical orders

---

### `history_deals_get(...) -> List[Deal]`

Get deals from history within a specified date range.

**Parameters:**
- Similar to `history_orders_get()`

**Returns:**
- `List[Deal]`: List of historical deals

---

## Resources

### `mt5://timeframes`

Available timeframe constants for use with market data functions.

### `mt5://tick_flags`

Tick flag constants for filtering tick data.

### `mt5://order_types`

Order type constants (BUY, SELL, BUY_LIMIT, etc.).

### `mt5://order_filling_types`

Order filling type constants (FOK, IOC, RETURN).

### `mt5://order_time_types`

Order time type constants (GTC, DAY, SPECIFIED, etc.).

### `mt5://trade_actions`

Trade action constants (DEAL, PENDING, SLTP, MODIFY, REMOVE, CLOSE_BY).

---

## Constants Reference

### Timeframes
- `1` - M1 (1 minute)
- `5` - M5 (5 minutes)
- `15` - M15 (15 minutes)
- `30` - M30 (30 minutes)
- `60` - H1 (1 hour)
- `240` - H4 (4 hours)
- `1440` - D1 (1 day)
- `10080` - W1 (1 week)
- `43200` - MN1 (1 month)

### Order Types
- `0` - ORDER_TYPE_BUY
- `1` - ORDER_TYPE_SELL
- `2` - ORDER_TYPE_BUY_LIMIT
- `3` - ORDER_TYPE_SELL_LIMIT
- `4` - ORDER_TYPE_BUY_STOP
- `5` - ORDER_TYPE_SELL_STOP

### Order Filling Types
- `0` - ORDER_FILLING_FOK (Fill or Kill)
- `1` - ORDER_FILLING_IOC (Immediate or Cancel)
- `2` - ORDER_FILLING_RETURN

### Trade Actions
- `0` - TRADE_ACTION_DEAL (Market order)
- `5` - TRADE_ACTION_PENDING (Pending order)
- `2` - TRADE_ACTION_SLTP (Modify SL/TP)
- `3` - TRADE_ACTION_MODIFY (Modify order)
- `4` - TRADE_ACTION_REMOVE (Remove order)
- `5` - TRADE_ACTION_CLOSE_BY (Close by opposite position)
