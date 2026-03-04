import logging
from datetime import datetime
from typing import Any

import MetaTrader5 as mt5
import pandas as pd
from fastmcp import FastMCP
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "MetaTrader 5 MCP Server",
    instructions="""
    This server is used to control MetaTrader 5 terminal.
    It provides a simple interface to interact with MetaTrader 5 terminal.
    """,
)


# Models for request/response data
class SymbolInfo(BaseModel):
    """Information about a trading symbol"""

    name: str
    description: str | None = None
    path: str | None = None
    session_deals: int | None = None
    session_buy_orders: int | None = None
    session_sell_orders: int | None = None
    volume: float | None = None
    volumehigh: float | None = None
    volumelow: float | None = None
    time: int | None = None
    digits: int | None = None
    spread: int | None = None
    spread_float: bool | None = None
    trade_calc_mode: int | None = None
    trade_mode: int | None = None
    start_time: int | None = None
    expiration_time: int | None = None
    trade_stops_level: int | None = None
    trade_freeze_level: int | None = None
    trade_exemode: int | None = None
    swap_mode: int | None = None
    swap_rollover3days: int | None = None
    margin_hedged_use_leg: bool | None = None
    expiration_mode: int | None = None
    filling_mode: int | None = None
    order_mode: int | None = None
    order_gtc_mode: int | None = None
    option_mode: int | None = None
    option_right: int | None = None
    bid: float | None = None
    bidhigh: float | None = None
    bidlow: float | None = None
    ask: float | None = None
    askhigh: float | None = None
    asklow: float | None = None
    last: float | None = None
    lasthigh: float | None = None
    lastlow: float | None = None
    point: float | None = None
    tick_value: float | None = None
    tick_value_profit: float | None = None
    tick_value_loss: float | None = None
    tick_size: float | None = None
    contract_size: float | None = None
    volume_min: float | None = None
    volume_max: float | None = None
    volume_step: float | None = None
    swap_long: float | None = None
    swap_short: float | None = None
    margin_initial: float | None = None
    margin_maintenance: float | None = None


class AccountInfo(BaseModel):
    """Trading account information"""

    login: int
    trade_mode: int
    leverage: int
    limit_orders: int
    margin_so_mode: int
    trade_allowed: bool
    trade_expert: bool
    margin_mode: int
    currency_digits: int
    fifo_close: bool
    balance: float
    credit: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    margin_so_call: float
    margin_so_so: float
    margin_initial: float
    margin_maintenance: float
    assets: float
    liabilities: float
    commission_blocked: float
    name: str
    server: str
    currency: str
    company: str


class OrderRequest(BaseModel):
    """
    Order request parameters for placing trades.

    Important: All type/action fields require INTEGER constants, not strings!

    Fields:
        action: Trade operation type as INTEGER:
            - 1: TRADE_ACTION_DEAL (Execute deal immediately)
            - 2: TRADE_ACTION_PENDING (Place pending order)
            - 5: TRADE_ACTION_SLTP (Modify SL/TP)
            - 6: TRADE_ACTION_MODIFY (Modify pending order)
            - 8: TRADE_ACTION_REMOVE (Remove pending order)

        symbol: Symbol name (e.g., "EURUSD", "XAUUSD")

        volume: Trade volume in lots (e.g., 0.01, 0.1, 1.0)

        type: Order type as INTEGER (NOT "market order" or "buy"):
            - 0: ORDER_TYPE_BUY (Buy market order)
            - 1: ORDER_TYPE_SELL (Sell market order)
            - 2: ORDER_TYPE_BUY_LIMIT (Buy limit order)
            - 3: ORDER_TYPE_SELL_LIMIT (Sell limit order)
            - 4: ORDER_TYPE_BUY_STOP (Buy stop order)
            - 5: ORDER_TYPE_SELL_STOP (Sell stop order)

        price: Order price (use current ask/bid for market orders)

        sl: Stop Loss price (optional)
        tp: Take Profit price (optional)
        deviation: Maximum price deviation in points (optional)
        magic: Expert Advisor ID (optional)
        comment: Order comment (optional, max 31 chars)
        type_time: Order expiration type (optional)
        type_filling: Order filling type as INTEGER (optional):
            - 0: ORDER_FILLING_FOK (Fill or Kill)
            - 1: ORDER_FILLING_IOC (Immediate or Cancel)
            - 2: ORDER_FILLING_RETURN (Return remaining)
    """

    action: int
    symbol: str
    volume: float
    type: int
    price: float
    sl: float | None = None
    tp: float | None = None
    deviation: int | None = None
    magic: int | None = None
    comment: str | None = None
    type_time: int | None = None
    type_filling: int | None = None

    @field_validator("volume")
    @classmethod
    def _vol_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("volume must be > 0 (in lots)")
        return v

    @field_validator("comment")
    @classmethod
    def _comment_len(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 31:
            raise ValueError("comment must be <= 31 characters")
        return v

    @field_validator("action")
    @classmethod
    def _action_valid(cls, v: int) -> int:
        allowed = {
            mt5.TRADE_ACTION_DEAL,
            mt5.TRADE_ACTION_PENDING,
            mt5.TRADE_ACTION_SLTP,
            mt5.TRADE_ACTION_MODIFY,
            mt5.TRADE_ACTION_REMOVE,
        }
        if v not in allowed:
            raise ValueError(f"action must be one of {sorted(allowed)}")
        return v


class OrderResult(BaseModel):
    """Order execution result"""

    retcode: int
    deal: int
    order: int
    volume: float
    price: float
    bid: float
    ask: float
    comment: str
    request_id: int
    retcode_external: int
    request: dict[str, Any]


class Position(BaseModel):
    """Trading position information"""

    ticket: int
    time: int
    time_msc: int
    time_update: int
    time_update_msc: int
    type: int
    magic: int
    identifier: int
    reason: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str


class HistoryOrder(BaseModel):
    """Historical order information"""

    ticket: int
    time_setup: int
    time_setup_msc: int
    time_expiration: int
    type: int
    type_time: int
    type_filling: int
    state: int
    magic: int
    position_id: int
    position_by_id: int
    reason: int
    volume_initial: float
    volume_current: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    price_stoplimit: float
    symbol: str
    comment: str
    external_id: str


class Deal(BaseModel):
    """Deal information"""

    ticket: int
    order: int
    time: int
    time_msc: int
    type: int
    entry: int
    magic: int
    position_id: int
    reason: int
    volume: float
    price: float
    commission: float
    swap: float
    profit: float
    fee: float
    symbol: str
    comment: str
    external_id: str


def _get_supported_filling_mode(symbol: str, action: int | None = None) -> int:
    """
    Get the supported filling mode for a symbol.

    Brokers support different order filling modes. This function checks the symbol's
    filling_mode bitmask and returns the best available option.

    Args:
        symbol: Symbol name (e.g., "EURUSD", "BTCUSD")
        action: Trade action type (optional). If mt5.TRADE_ACTION_PENDING (2),
                always returns mt5.ORDER_FILLING_RETURN (2).

    Returns:
        int: Filling mode constant (mt5.ORDER_FILLING_FOK=0, mt5.ORDER_FILLING_IOC=1, mt5.ORDER_FILLING_RETURN=2)
             Defaults to mt5.ORDER_FILLING_IOC if unable to determine.
    """
    # Pending orders always use RETURN filling mode
    if action is not None and action == mt5.TRADE_ACTION_PENDING:
        return mt5.ORDER_FILLING_RETURN

    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return mt5.ORDER_FILLING_IOC  # Default to IOC

        # filling_mode is a bitmask: 1=FOK, 2=IOC, 4=reserved (not used in standard MT5)
        # Note: RETURN (2) is NOT a symbol filling mode - it's used for pending orders
        filling_mask = getattr(symbol_info, "filling_mode", 0)

        # Priority: IOC > FOK > RETURN (for non-market execution)
        if filling_mask & 2:  # IOC supported?
            return mt5.ORDER_FILLING_IOC
        elif filling_mask & 1:  # FOK supported?
            return mt5.ORDER_FILLING_FOK
        else:
            # For non-market execution symbols, RETURN may be valid
            # SYMBOL_TRADE_EXECUTION_MARKET = 2 (not exposed in Python API)
            trade_exemode = getattr(symbol_info, "trade_exemode", None)
            if trade_exemode != 2:  # Not market execution
                return mt5.ORDER_FILLING_RETURN
            return mt5.ORDER_FILLING_IOC  # Default to IOC for market execution
    except Exception:
        return mt5.ORDER_FILLING_IOC  # Default to IOC on any error


def _ensure_type_filling(request_dict: dict[str, Any]) -> None:
    """
    Ensure type_filling is set in the request dictionary.

    Auto-detects the appropriate filling mode based on symbol and action
    if not already provided by the user.

    Args:
        request_dict: The order request dictionary to modify in-place.
    """
    if "type_filling" in request_dict or "symbol" not in request_dict:
        return

    symbol = request_dict["symbol"]
    action = request_dict.get("action")
    filling_mode = _get_supported_filling_mode(symbol, action)
    request_dict["type_filling"] = filling_mode
    logger.info(f"Auto-selected filling mode {filling_mode} for {symbol}")


def _format_timestamps_to_iso8601_utc(df: pd.DataFrame) -> None:
    """
    Convert timestamp columns in a DataFrame to ISO 8601 UTC format strings.

    Modifies the DataFrame in-place, converting:
    - 'time' column: seconds -> ISO 8601 with Z suffix (e.g., "2024-01-22T10:00:00Z")
    - 'time_msc' column: milliseconds -> ISO 8601 with milliseconds and Z suffix (e.g., "2024-01-22T10:00:00.123Z")

    Args:
        df: DataFrame containing timestamp columns to format
    """
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    if "time_msc" in df.columns:
        # Convert milliseconds to datetime, then format with millisecond precision
        dt_series = pd.to_datetime(df["time_msc"], unit="ms", utc=True)
        # Format with milliseconds (3 digits) instead of microseconds (6 digits)
        df["time_msc"] = (
            dt_series.dt.strftime("%Y-%m-%dT%H:%M:%S")
            + "."
            + (df["time_msc"] % 1000).astype(str).str.zfill(3)
            + "Z"
        )


timeframe_map = {
    # Minutes
    1: mt5.TIMEFRAME_M1,  # 1 minute
    2: mt5.TIMEFRAME_M2,  # 2 minutes
    3: mt5.TIMEFRAME_M3,  # 3 minutes
    4: mt5.TIMEFRAME_M4,  # 4 minutes
    5: mt5.TIMEFRAME_M5,  # 5 minutes
    6: mt5.TIMEFRAME_M6,  # 6 minutes
    10: mt5.TIMEFRAME_M10,  # 10 minutes
    12: mt5.TIMEFRAME_M12,  # 12 minutes
    15: mt5.TIMEFRAME_M15,  # 15 minutes
    20: mt5.TIMEFRAME_M20,  # 20 minutes
    30: mt5.TIMEFRAME_M30,  # 30 minutes
    # Hours
    60: mt5.TIMEFRAME_H1,  # 1 hour
    120: mt5.TIMEFRAME_H2,  # 2 hours
    180: mt5.TIMEFRAME_H3,  # 3 hours
    240: mt5.TIMEFRAME_H4,  # 4 hours
    360: mt5.TIMEFRAME_H6,  # 6 hours
    480: mt5.TIMEFRAME_H8,  # 8 hours
    720: mt5.TIMEFRAME_H12,  # 12 hours
    # Days/Weeks/Months
    1440: mt5.TIMEFRAME_D1,  # 1 day
    10080: mt5.TIMEFRAME_W1,  # 1 week
    43200: mt5.TIMEFRAME_MN1,  # 1 month
}


def get_timeframe_constant(timeframe: int) -> int:
    """
    Convert user-friendly timeframe integer to MT5 constant with validation.

    Args:
        timeframe: Timeframe in minutes (e.g., 60 for H1)

    Returns:
        MT5 timeframe constant

    Raises:
        ValueError: If timeframe is not supported
    """
    if timeframe not in timeframe_map:
        supported = ", ".join(str(k) for k in sorted(timeframe_map.keys()))
        raise ValueError(
            f"Unsupported timeframe: {timeframe}. Supported timeframes (in minutes): {supported}"
        )
    return timeframe_map[timeframe]


# Initialize MetaTrader 5 connection
@mcp.tool()
def initialize(path: str) -> bool:
    """
    Initialize the MetaTrader 5 terminal.

    This MUST be called first before using any other MT5 tools.
    Establishes connection to the MT5 terminal application.

    Args:
        path: Full path to the MT5 terminal executable.
              Common paths:
              - "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
              - "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe"

    Returns:
        bool: True if initialization was successful, False otherwise.

    Example:
        # Initialize MT5 connection first
        initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe")
        # Now you can use other tools like get_account_info(), symbol_select(), etc.
    """
    if not mt5.initialize(path=path):
        logger.error(f"MT5 initialization failed, error code: {mt5.last_error()}")
        return False

    logger.info("MT5 initialized successfully")
    return True


# Shutdown MetaTrader 5 connection
@mcp.tool()
def shutdown() -> bool:
    """
    Shut down the connection to the MetaTrader 5 terminal.

    Returns:
        bool: True if shutdown was successful.
    """
    mt5.shutdown()
    logger.info("MT5 connection shut down")
    return True


# Login to MetaTrader 5 account
@mcp.tool()
def login(login: int, password: str, server: str) -> bool:
    """
    Log in to the MetaTrader 5 trading account.

    Call this AFTER initialize() if you need to switch accounts or login programmatically.
    Not required if MT5 terminal is already logged in to an account.

    Args:
        login: Trading account number (integer, e.g., 12345678)
        password: Trading account password (string)
        server: Trading server name (e.g., "Demo-Server", "YourBroker-Live")

    Returns:
        bool: True if login was successful, False otherwise.

    Example:
        # First initialize MT5
        initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe")
        # Then login to your account
        login(login=12345678, password="yourpassword", server="Demo-Server")
        # Now you can use get_account_info(), place trades, etc.
    """
    if not mt5.login(login=login, password=password, server=server):
        logger.error(f"MT5 login failed, error code: {mt5.last_error()}")
        return False

    logger.info(f"MT5 login successful to account #{login} on server {server}")
    return True


# Get account information
@mcp.tool()
def get_account_info() -> AccountInfo:
    """
    Get information about the current trading account.

    Important: Requires MT5 to be initialized and logged in.
    If this fails, ensure you have:
    1. Called initialize() first
    2. Logged in using login() if using a demo/live account
    3. Have an active connection to the terminal

    Returns:
        AccountInfo: Information about the trading account including balance, equity,
                     margin, profit, etc.

    Raises:
        ValueError: If account info cannot be retrieved. Common causes:
            - MT5 not initialized: Call initialize() first
            - Not logged in: Call login() with your credentials
            - Terminal not connected: Check MT5 connection status
    """
    account_info = mt5.account_info()
    if account_info is None:
        error_code, error_msg = mt5.last_error()
        logger.error(f"Failed to get account info, error: {error_code} - {error_msg}")
        raise ValueError(
            f"Failed to get account info. Error: {error_code} - {error_msg}. "
            f"Possible causes:\n"
            f"1. MT5 not initialized - Call initialize() first\n"
            f"2. Not logged in - Call login() with your credentials\n"
            f"3. Terminal not connected - Check MT5 terminal status\n"
            f"4. No active trading account - Ensure an account is configured in MT5"
        )

    # Convert named tuple to dictionary
    account_dict = account_info._asdict()
    return AccountInfo(**account_dict)


# Get terminal information
@mcp.tool()
def get_terminal_info() -> dict[str, Any]:
    """
    Get information about the MetaTrader 5 terminal.

    Returns:
        Dict[str, Any]: Information about the terminal.
    """
    terminal_info = mt5.terminal_info()
    if terminal_info is None:
        logger.error(f"Failed to get terminal info, error code: {mt5.last_error()}")
        raise ValueError("Failed to get terminal info")

    # Convert named tuple to dictionary
    return terminal_info._asdict()


# Get version information
@mcp.tool()
def get_version() -> dict[str, Any]:
    """
    Get the MetaTrader 5 version.

    Returns:
        Dict[str, Any]: Version information.
    """
    version = mt5.version()
    if version is None:
        logger.error(f"Failed to get version, error code: {mt5.last_error()}")
        raise ValueError("Failed to get version")

    return {"version": version[0], "build": version[1], "date": version[2]}


# Get symbols
@mcp.tool()
def get_symbols() -> list[str]:
    """
    Get all available symbols (financial instruments) from the MetaTrader 5 terminal.

    Returns:
        List[str]: List of symbol names.
    """
    symbols = mt5.symbols_get()
    if symbols is None:
        logger.error(f"Failed to get symbols, error code: {mt5.last_error()}")
        raise ValueError("Failed to get symbols")

    return [symbol.name for symbol in symbols]


# Get symbols by group
@mcp.tool()
def get_symbols_by_group(group: str) -> list[str]:
    """
    Get symbols that match a specific group or pattern.

    Args:
        group: Filter for arranging a group of symbols (e.g., "*", "EUR*", etc.)

    Returns:
        List[str]: List of symbol names that match the group.
    """
    symbols = mt5.symbols_get(group=group)
    if symbols is None:
        logger.error(f"Failed to get symbols for group {group}, error code: {mt5.last_error()}")
        return []

    return [symbol.name for symbol in symbols]


# Get symbol information
@mcp.tool()
def get_symbol_info(symbol: str) -> SymbolInfo:
    """
    Get information about a specific symbol.

    Args:
        symbol: Symbol name

    Returns:
        SymbolInfo: Information about the symbol.
    """
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error(f"Failed to get info for symbol {symbol}, error code: {mt5.last_error()}")
        raise ValueError(f"Failed to get info for symbol {symbol}")

    # Convert named tuple to dictionary
    symbol_dict = symbol_info._asdict()
    return SymbolInfo(**symbol_dict)


# Get symbol tick information
@mcp.tool()
def get_symbol_info_tick(symbol: str) -> dict[str, Any]:
    """
    Get the latest tick data for a symbol.

    Important: The symbol must be selected/visible in Market Watch.
    If this fails, try calling symbol_select() first to add the symbol.

    Args:
        symbol: Symbol name (e.g., "EURUSD", "XAUUSD", "GBPUSD")

    Returns:
        Dict[str, Any]: Latest tick data with fields: time, bid, ask, last, volume, etc.

    Raises:
        ValueError: If the symbol is not found or not selected in Market Watch.
            Try calling symbol_select(symbol="{symbol}", visible=True) first.
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        error_code, error_msg = mt5.last_error()
        logger.error(f"Failed to get tick for symbol {symbol}, error: {error_code} - {error_msg}")
        raise ValueError(
            f"Failed to get tick for symbol {symbol}. "
            f"Error: {error_code} - {error_msg}. "
            f"The symbol may not be selected in Market Watch. "
            f"Try calling symbol_select(symbol='{symbol}', visible=True) first, "
            f"or check if the symbol name is correct and available with your broker."
        )

    # Convert named tuple to dictionary
    return tick._asdict()


# Select symbol in Market Watch
@mcp.tool()
def symbol_select(symbol: str, visible: bool = True) -> bool:
    """
    Select a symbol in the Market Watch window or remove a symbol from it.

    This is REQUIRED before you can get tick data or trade a symbol.
    If get_symbol_info_tick() or other symbol operations fail, call this first.

    Args:
        symbol: Symbol name (e.g., "EURUSD", "XAUUSD", "GBPUSD")
        visible: Symbol visibility flag
            - True: Add/show the symbol in Market Watch (default, recommended)
            - False: Hide the symbol from Market Watch

    Returns:
        bool: True if the symbol is selected successfully, False otherwise.

    Example:
        # Before getting tick data for XAUUSD:
        symbol_select(symbol="XAUUSD", visible=True)
        tick = get_symbol_info_tick(symbol="XAUUSD")
    """
    result = mt5.symbol_select(symbol, visible)
    if not result:
        logger.error(f"Failed to select symbol {symbol}, error code: {mt5.last_error()}")

    return result


# Copy rates from position
@mcp.tool()
def copy_rates_from_pos(
    symbol: str, timeframe: int, start_pos: int, count: int
) -> list[dict[str, Any]]:
    """
    Get bars from a specified symbol and timeframe starting from the specified position.

    Args:
        symbol: Symbol name (e.g., "EURUSD", "GBPUSD")
        timeframe: Timeframe in minutes as an INTEGER:
            - 1: TIMEFRAME_M1 (1 minute)
            - 5: TIMEFRAME_M5 (5 minutes)
            - 15: TIMEFRAME_M15 (15 minutes)
            - 30: TIMEFRAME_M30 (30 minutes)
            - 60: TIMEFRAME_H1 (1 hour)
            - 240: TIMEFRAME_H4 (4 hours)
            - 1440: TIMEFRAME_D1 (1 day)
            - 10080: TIMEFRAME_W1 (1 week)
            - 43200: TIMEFRAME_MN1 (1 month)
        start_pos: Starting position as an INTEGER (0 = most recent bar, 1 = second most recent, etc.)
        count: Number of bars to retrieve as an INTEGER (e.g., 100 for last 100 bars)

    Example:
        To get the last 100 bars: start_pos=0, count=100
        To get bars 10-20 from the end: start_pos=10, count=10

    Returns:
        List[Dict[str, Any]]: List of bars with time, open, high, low, close, tick_volume, spread, and real_volume.
    """
    rates = mt5.copy_rates_from_pos(symbol, get_timeframe_constant(timeframe), start_pos, count)
    if rates is None:
        logger.error(f"Failed to copy rates for {symbol}, error code: {mt5.last_error()}")
        raise ValueError(f"Failed to copy rates for {symbol}")

    # Convert numpy array to list of dictionaries
    df = pd.DataFrame(rates)
    # Convert timestamps to ISO 8601 UTC format for JSON serialization
    _format_timestamps_to_iso8601_utc(df)

    return df.to_dict("records")


# Copy rates from date
@mcp.tool()
def copy_rates_from_date(
    symbol: str, timeframe: int, date_from: datetime, count: int
) -> list[dict[str, Any]]:
    """
    Get bars from a specified symbol and timeframe starting from the specified date.

    Args:
        symbol: Symbol name
        timeframe: Timeframe (use TIMEFRAME_* constants)
        date_from: Start date for bar retrieval
        count: Number of bars to retrieve

    Returns:
        List[Dict[str, Any]]: List of bars with time, open, high, low, close, tick_volume, spread, and real_volume.
    """
    rates = mt5.copy_rates_from_date(symbol, get_timeframe_constant(timeframe), date_from, count)
    if rates is None:
        logger.error(
            f"Failed to copy rates for {symbol} from date {date_from}, error code: {mt5.last_error()}"
        )
        raise ValueError(f"Failed to copy rates for {symbol} from date {date_from}")

    # Convert numpy array to list of dictionaries
    df = pd.DataFrame(rates)
    # Convert timestamps to ISO 8601 UTC format for JSON serialization
    _format_timestamps_to_iso8601_utc(df)

    return df.to_dict("records")


# Copy rates range
@mcp.tool()
def copy_rates_range(
    symbol: str, timeframe: int, date_from: datetime, date_to: datetime
) -> list[dict[str, Any]]:
    """
    Get bars from a specified symbol and timeframe within the specified date range.

    Args:
        symbol: Symbol name
        timeframe: Timeframe (use TIMEFRAME_* constants)
        date_from: Start date for bar retrieval
        date_to: End date for bar retrieval

    Returns:
        List[Dict[str, Any]]: List of bars with time, open, high, low, close, tick_volume, spread, and real_volume.
    """
    rates = mt5.copy_rates_range(symbol, get_timeframe_constant(timeframe), date_from, date_to)
    if rates is None:
        logger.error(
            f"Failed to copy rates for {symbol} in range {date_from} to {date_to}, error code: {mt5.last_error()}"
        )
        raise ValueError(f"Failed to copy rates for {symbol} in range {date_from} to {date_to}")

    # Convert numpy array to list of dictionaries
    df = pd.DataFrame(rates)
    # Convert timestamps to ISO 8601 UTC format for JSON serialization
    _format_timestamps_to_iso8601_utc(df)

    return df.to_dict("records")


# Copy ticks from position
@mcp.tool()
def copy_ticks_from_pos(
    symbol: str, start_time: datetime, count: int, flags: int = mt5.COPY_TICKS_ALL
) -> list[dict[str, Any]]:
    """
    Get ticks from a specified symbol starting from the specified position.

    Args:
        symbol: Symbol name
        start_time: Initial time for tick retrieval
        count: Number of ticks to retrieve
        flags: Type of requested ticks:
            - mt5.COPY_TICKS_ALL: All ticks (default)
            - mt5.COPY_TICKS_INFO: Ticks containing bid and/or ask price changes
            - mt5.COPY_TICKS_TRADE: Ticks containing last price and volume changes

    Returns:
        List[Dict[str, Any]]: List of ticks.
    """
    ticks = mt5.copy_ticks_from(symbol, start_time, count, flags)
    if ticks is None:
        logger.error(f"Failed to copy ticks for {symbol}, error code: {mt5.last_error()}")
        raise ValueError(f"Failed to copy ticks for {symbol}")

    # Convert numpy array to list of dictionaries
    df = pd.DataFrame(ticks)
    # Convert timestamps to ISO 8601 UTC format for JSON serialization
    _format_timestamps_to_iso8601_utc(df)

    return df.to_dict("records")


# Copy ticks from date
@mcp.tool()
def copy_ticks_from_date(
    symbol: str, date_from: datetime, count: int, flags: int = mt5.COPY_TICKS_ALL
) -> list[dict[str, Any]]:
    """
    Get ticks from a specified symbol starting from the specified date.

    Args:
        symbol: Symbol name
        date_from: Start date for tick retrieval
        count: Number of ticks to retrieve
        flags: Type of requested ticks

    Returns:
        List[Dict[str, Any]]: List of ticks.
    """
    ticks = mt5.copy_ticks_from(symbol, date_from, count, flags)
    if ticks is None:
        logger.error(
            f"Failed to copy ticks for {symbol} from date {date_from}, error code: {mt5.last_error()}"
        )
        raise ValueError(f"Failed to copy ticks for {symbol} from date {date_from}")

    # Convert numpy array to list of dictionaries
    df = pd.DataFrame(ticks)
    # Convert timestamps to ISO 8601 UTC format for JSON serialization
    _format_timestamps_to_iso8601_utc(df)

    return df.to_dict("records")


# Copy ticks range
@mcp.tool()
def copy_ticks_range(
    symbol: str, date_from: datetime, date_to: datetime, flags: int = mt5.COPY_TICKS_ALL
) -> list[dict[str, Any]]:
    """
    Get ticks from a specified symbol within the specified date range.

    Args:
        symbol: Symbol name
        date_from: Start date for tick retrieval
        date_to: End date for tick retrieval
        flags: Type of requested ticks

    Returns:
        List[Dict[str, Any]]: List of ticks.
    """
    ticks = mt5.copy_ticks_range(symbol, date_from, date_to, flags)
    if ticks is None:
        logger.error(
            f"Failed to copy ticks for {symbol} in range {date_from} to {date_to}, error code: {mt5.last_error()}"
        )
        raise ValueError(f"Failed to copy ticks for {symbol} in range {date_from} to {date_to}")

    # Convert numpy array to list of dictionaries
    df = pd.DataFrame(ticks)
    # Convert timestamps to ISO 8601 UTC format for JSON serialization
    _format_timestamps_to_iso8601_utc(df)

    return df.to_dict("records")


# Get last error
@mcp.tool()
def get_last_error() -> dict[str, Any]:
    """
    Get the last error code and description.

    Returns:
        Dict[str, Any]: Last error code and description.
    """
    error_code, error_message = mt5.last_error()

    error_descriptions = {
        mt5.RES_S_OK: "OK",
        mt5.RES_E_FAIL: "Generic fail",
        mt5.RES_E_INVALID_PARAMS: "Invalid parameters",
        mt5.RES_E_NO_MEMORY: "No memory",
        mt5.RES_E_NOT_FOUND: "Not found",
        mt5.RES_E_INVALID_VERSION: "Invalid version",
        mt5.RES_E_AUTH_FAILED: "Authorization failed",
        mt5.RES_E_UNSUPPORTED: "Unsupported method",
        mt5.RES_E_AUTO_TRADING_DISABLED: "Auto-trading disabled",
        mt5.RES_E_INTERNAL_FAIL: "Internal failure",
    }

    error_description = error_descriptions.get(error_code, error_message or "Unknown error")

    return {"code": error_code, "description": error_description}


# Resource for timeframe constants
@mcp.resource("mt5://timeframes")
def get_timeframes() -> str:
    """
    Get information about available timeframes in MetaTrader 5.

    Returns:
        str: Information about available timeframes.
    """
    timeframes = {
        "TIMEFRAME_M1": 1,
        "TIMEFRAME_M2": 2,
        "TIMEFRAME_M3": 3,
        "TIMEFRAME_M4": 4,
        "TIMEFRAME_M5": 5,
        "TIMEFRAME_M6": 6,
        "TIMEFRAME_M10": 10,
        "TIMEFRAME_M12": 12,
        "TIMEFRAME_M15": 15,
        "TIMEFRAME_M20": 20,
        "TIMEFRAME_M30": 30,
        "TIMEFRAME_H1": 60,
        "TIMEFRAME_H2": 120,
        "TIMEFRAME_H3": 180,
        "TIMEFRAME_H4": 240,
        "TIMEFRAME_H6": 360,
        "TIMEFRAME_H8": 480,
        "TIMEFRAME_H12": 720,
        "TIMEFRAME_D1": 1440,
        "TIMEFRAME_W1": 10080,
        "TIMEFRAME_MN1": 43200,
    }

    result = "Available timeframes in MetaTrader 5:\n\n"
    for name, value in timeframes.items():
        result += f"{name}: {value}\n"

    return result


# Resource for tick flag constants
@mcp.resource("mt5://tick_flags")
def get_tick_flags() -> str:
    """
    Get information about tick flags in MetaTrader 5.

    Returns:
        str: Information about tick flags.
    """
    tick_flags = {
        "COPY_TICKS_ALL": mt5.COPY_TICKS_ALL,
        "COPY_TICKS_INFO": mt5.COPY_TICKS_INFO,
        "COPY_TICKS_TRADE": mt5.COPY_TICKS_TRADE,
    }

    result = "Available tick flags in MetaTrader 5:\n\n"
    for name, value in tick_flags.items():
        result += f"{name}: {value}\n"

    return result


# Send order
@mcp.tool()
def order_send(request: OrderRequest) -> OrderResult:
    """
    Send an order to the trade server.

    CRITICAL REQUIREMENTS:
    1. Pass order fields DIRECTLY - do NOT wrap in "request" key
    2. Use INTEGER constants for action, type, type_filling - NO STRINGS
    3. Volume is in LOTS (0.01, 0.1, 1.0), NOT contract units (100000)
    4. Do NOT include unsupported fields like "group"
    5. action must be 1 or 2 (NOT 0)

    Common Mistakes to Avoid:
    - ❌ {"request": {"action": 1, ...}} → ✅ {"action": 1, ...}
    - ❌ "action": 0 → ✅ "action": 1 (for market) or 2 (for pending)
    - ❌ "action": "buy" → ✅ "action": 1
    - ❌ "type": "limit" → ✅ "type": 2
    - ❌ "volume": 100000 → ✅ "volume": 0.1
    - ❌ request: "{...json...}" → ✅ request: {...object...}

    Args:
        request: OrderRequest object with these fields:
            REQUIRED:
            - action (int): 1=TRADE_ACTION_DEAL, 2=TRADE_ACTION_PENDING
            - symbol (str): e.g., "EURUSD"
            - volume (float): Lots, e.g., 0.01 (micro), 0.1 (mini), 1.0 (standard)
            - type (int): 0=BUY, 1=SELL, 2=BUY_LIMIT, 3=SELL_LIMIT, etc.
            - price (float): Order price

            OPTIONAL (omit if not needed, don't set to None or 0):
            - sl (float): Stop loss price
            - tp (float): Take profit price
            - deviation (int): Max price deviation in points
            - magic (int): EA identifier
            - comment (str): Max 31 characters
            - type_time (int): Expiration type
            - type_filling (int): 0=FOK, 1=IOC, 2=RETURN (omit to use default)

    Returns:
        OrderResult: Order execution result with return code, deal, order info.

    Example 1 - Market Buy Order (with all optional fields):
        {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
            "price": 1.1850,
            "sl": 1.1800,
            "tp": 1.1900,
            "deviation": 20,
            "magic": 123456,
            "comment": "Buy order",
            "type_filling": 2
        }

    Example 2 - Market Buy Order (minimal - only required fields):
        {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
            "price": 1.1850
        }

    Example 3 - Buy Limit Order (pending):
        {
            "action": 2,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 2,
            "price": 1.3000,
            "sl": 1.2950,
            "tp": 1.3050
        }

    WRONG - Do NOT do this:
        {
            "request": {          ← Extra nesting!
                "action": 1,
                ...
            }
        }
    """
    # Convert request to dictionary and exclude None values
    # MT5 doesn't accept None for optional parameters - they must be omitted entirely
    request_dict = request.model_dump(exclude_none=True)

    # Auto-detect filling mode if not provided
    _ensure_type_filling(request_dict)

    # Send order
    result = mt5.order_send(request_dict)
    if result is None:
        error_code, error_msg = mt5.last_error()
        logger.error(f"Failed to send order, error: {error_code} - {error_msg}")
        raise ValueError(
            f"Failed to send order. MT5 Error {error_code}: {error_msg}\n"
            f"Request: {request_dict}\n"
            f"Common causes:\n"
            f"- MT5 not initialized: Call initialize() first\n"
            f"- Invalid symbol: Check symbol name and ensure it's selected\n"
            f"- Invalid price: Ensure price is current (use get_symbol_info_tick)\n"
            f"- Insufficient margin: Check account balance\n"
            f"- Market closed: Check if trading is allowed\n"
            f"- Auto-trading disabled: Enable in MT5 terminal\n"
            f"- Invalid volume: Check min/max/step volume for the symbol"
        )

    # Convert named tuple to dictionary
    result_dict = result._asdict()

    # Define MT5 success retcodes - these are NOT errors
    success_retcodes = {
        mt5.TRADE_RETCODE_DONE,  # 10009 - Order placed successfully (market order)
        mt5.TRADE_RETCODE_PLACED,  # 10008 - Order placed (pending order)
        mt5.TRADE_RETCODE_DONE_PARTIAL,  # 10010 - Partial fill (rest canceled)
    }

    # Check if order execution failed (retcode not in success set)
    retcode = result_dict.get("retcode")
    if retcode not in success_retcodes:
        comment = result_dict.get("comment", "Unknown error")
        logger.error(f"Order execution failed with retcode {retcode}: {comment}")

        # Map common error retcodes to helpful messages
        retcode_messages = {
            mt5.TRADE_RETCODE_REQUOTE: "TRADE_RETCODE_REQUOTE - Requote. Price changed, retry with new price",
            mt5.TRADE_RETCODE_REJECT: "TRADE_RETCODE_REJECT - Request rejected by broker",
            mt5.TRADE_RETCODE_CANCEL: "TRADE_RETCODE_CANCEL - Request canceled by trader",
            mt5.TRADE_RETCODE_ERROR: "TRADE_RETCODE_ERROR - Request processing error",
            mt5.TRADE_RETCODE_TIMEOUT: "TRADE_RETCODE_TIMEOUT - Request timeout",
            mt5.TRADE_RETCODE_INVALID: "TRADE_RETCODE_INVALID - Invalid request",
            mt5.TRADE_RETCODE_INVALID_VOLUME: "TRADE_RETCODE_INVALID_VOLUME - Invalid volume",
            mt5.TRADE_RETCODE_INVALID_PRICE: "TRADE_RETCODE_INVALID_PRICE - Invalid price",
            mt5.TRADE_RETCODE_INVALID_STOPS: "TRADE_RETCODE_INVALID_STOPS - Invalid stops (SL/TP)",
            mt5.TRADE_RETCODE_TRADE_DISABLED: "TRADE_RETCODE_TRADE_DISABLED - Trading disabled",
            mt5.TRADE_RETCODE_MARKET_CLOSED: "TRADE_RETCODE_MARKET_CLOSED - Market is closed",
            mt5.TRADE_RETCODE_NO_MONEY: "TRADE_RETCODE_NO_MONEY - Not enough money",
            mt5.TRADE_RETCODE_PRICE_CHANGED: "TRADE_RETCODE_PRICE_CHANGED - Price changed, retry",
            mt5.TRADE_RETCODE_PRICE_OFF: "TRADE_RETCODE_PRICE_OFF - No prices (broker not providing quotes)",
            mt5.TRADE_RETCODE_INVALID_EXPIRATION: "TRADE_RETCODE_INVALID_EXPIRATION - Invalid order expiration",
            mt5.TRADE_RETCODE_ORDER_CHANGED: "TRADE_RETCODE_ORDER_CHANGED - Order state changed",
            mt5.TRADE_RETCODE_TOO_MANY_REQUESTS: "TRADE_RETCODE_TOO_MANY_REQUESTS - Too many requests",
            mt5.TRADE_RETCODE_NO_CHANGES: "TRADE_RETCODE_NO_CHANGES - No changes in request",
            mt5.TRADE_RETCODE_SERVER_DISABLES_AT: "TRADE_RETCODE_SERVER_DISABLES_AT - Autotrading disabled by server",
            mt5.TRADE_RETCODE_CLIENT_DISABLES_AT: "TRADE_RETCODE_CLIENT_DISABLES_AT - Autotrading disabled by client",
            mt5.TRADE_RETCODE_LOCKED: "TRADE_RETCODE_LOCKED - Request locked for processing",
            mt5.TRADE_RETCODE_FROZEN: "TRADE_RETCODE_FROZEN - Order/position frozen",
            mt5.TRADE_RETCODE_INVALID_FILL: "TRADE_RETCODE_INVALID_FILL - Invalid filling type",
        }

        detailed_msg = retcode_messages.get(retcode, f"Unknown retcode {retcode}")
        raise ValueError(
            f"Order execution failed: {detailed_msg}\n"
            f"Comment from broker: {comment}\n"
            f"Request: {request_dict}\n"
            f"Result: {result_dict}"
        )

    # Convert request named tuple to dictionary if needed
    if hasattr(result_dict["request"], "_asdict"):
        result_dict["request"] = result_dict["request"]._asdict()

    return OrderResult(**result_dict)


# Check order
@mcp.tool()
def order_check(request: OrderRequest) -> dict[str, Any]:
    """
    Check if an order can be placed with the specified parameters.

    Use this BEFORE order_send() to validate the order without executing it.
    Follows the same requirements as order_send():
    - request must be an OBJECT (dict), not a JSON string
    - Use INTEGER constants for action, type, type_filling
    - Volume in LOTS (0.01, 0.1, 1.0), not contract units

    Args:
        request: OrderRequest object (same format as order_send)
                See order_send() documentation for field details and examples.

    Returns:
        Dict[str, Any]: Order check result with retcode, balance, equity, margin, etc.
            - retcode: 0 if check passed, error code otherwise
            - balance: Account balance after order
            - equity: Account equity after order
            - margin: Required margin
            - margin_free: Free margin after order
            - comment: Error description if check failed

    Example:
        # Check before sending
        result = order_check(request={
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
            "price": 1.1850,
            "type_filling": 2
        })
        if result["retcode"] == 0:
            # OK to send the order
            order_send(request={...})
    """
    # Convert request to dictionary and exclude None values
    # MT5 doesn't accept None for optional parameters - they must be omitted entirely
    request_dict = request.model_dump(exclude_none=True)

    # Auto-detect filling mode if not provided
    _ensure_type_filling(request_dict)

    # Check order
    result = mt5.order_check(request_dict)
    if result is None:
        error_code, error_msg = mt5.last_error()
        logger.error(f"Failed to check order, error: {error_code} - {error_msg}")
        raise ValueError(
            f"Failed to check order. MT5 Error {error_code}: {error_msg}\n"
            f"Request: {request_dict}\n"
            f"Common causes:\n"
            f"- MT5 not initialized: Call initialize() first\n"
            f"- Invalid parameters: Check symbol, volume, price, etc."
        )

    # Convert named tuple to dictionary
    result_dict = result._asdict()

    # Convert request named tuple to dictionary if needed
    if hasattr(result_dict["request"], "_asdict"):
        result_dict["request"] = result_dict["request"]._asdict()

    return result_dict


# Get positions
@mcp.tool()
def positions_get(symbol: str | None = None, group: str | None = None) -> list[Position]:
    """
    Get open positions.

    Args:
        symbol: Symbol name. If specified, only positions for this symbol will be returned.
        group: Filter for arranging a group of positions (e.g., "*", "USD*", etc.)

    Returns:
        List[Position]: List of open positions.
    """
    if symbol is not None:
        positions = mt5.positions_get(symbol=symbol)
    elif group is not None:
        positions = mt5.positions_get(group=group)
    else:
        positions = mt5.positions_get()

    if positions is None:
        logger.error(f"Failed to get positions, error code: {mt5.last_error()}")
        return []

    result = []
    for position in positions:
        # Convert named tuple to dictionary
        position_dict = position._asdict()
        result.append(Position(**position_dict))

    return result


# Get position by ticket
@mcp.tool()
def positions_get_by_ticket(ticket: int) -> Position | None:
    """
    Get an open position by its ticket.

    Args:
        ticket: Position ticket

    Returns:
        Optional[Position]: Position information or None if not found.
    """
    position = mt5.positions_get(ticket=ticket)
    if position is None or len(position) == 0:
        logger.error(f"Failed to get position with ticket {ticket}, error code: {mt5.last_error()}")
        return None

    # Convert named tuple to dictionary
    position_dict = position[0]._asdict()
    return Position(**position_dict)


# Get orders
@mcp.tool()
def orders_get(symbol: str | None = None, group: str | None = None) -> list[dict[str, Any]]:
    """
    Get active orders.

    Args:
        symbol: Symbol name. If specified, only orders for this symbol will be returned.
        group: Filter for arranging a group of orders (e.g., "*", "USD*", etc.)

    Returns:
        List[Dict[str, Any]]: List of active orders.
    """
    if symbol is not None:
        orders = mt5.orders_get(symbol=symbol)
    elif group is not None:
        orders = mt5.orders_get(group=group)
    else:
        orders = mt5.orders_get()

    if orders is None:
        logger.error(f"Failed to get orders, error code: {mt5.last_error()}")
        return []

    result = []
    for order in orders:
        # Convert named tuple to dictionary
        order_dict = order._asdict()
        result.append(order_dict)

    return result


# Get order by ticket
@mcp.tool()
def orders_get_by_ticket(ticket: int) -> dict[str, Any] | None:
    """
    Get an active order by its ticket.

    Args:
        ticket: Order ticket

    Returns:
        Optional[Dict[str, Any]]: Order information or None if not found.
    """
    order = mt5.orders_get(ticket=ticket)
    if order is None or len(order) == 0:
        logger.error(f"Failed to get order with ticket {ticket}, error code: {mt5.last_error()}")
        return None

    # Convert named tuple to dictionary
    return order[0]._asdict()


# Get history orders
@mcp.tool()
def history_orders_get(
    symbol: str | None = None,
    group: str | None = None,
    ticket: int | None = None,
    position: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[HistoryOrder]:
    """
    Get orders from history within the specified date range.

    Args:
        symbol: Symbol name
        group: Filter for arranging a group of orders
        ticket: Order ticket
        position: Position ticket
        from_date: Start date for order retrieval
        to_date: End date for order retrieval

    Returns:
        List[HistoryOrder]: List of historical orders.
    """
    request = {}
    if symbol is not None:
        request["symbol"] = symbol
    if group is not None:
        request["group"] = group
    if ticket is not None:
        request["ticket"] = ticket
    if position is not None:
        request["position"] = position
    if from_date is not None:
        request["from"] = from_date
    if to_date is not None:
        request["to"] = to_date

    # Get history orders
    if request:
        orders = mt5.history_orders_get(**request)
    else:
        orders = mt5.history_orders_get()

    if orders is None:
        logger.error(f"Failed to get history orders, error code: {mt5.last_error()}")
        return []

    result = []
    for order in orders:
        # Convert named tuple to dictionary
        order_dict = order._asdict()
        result.append(HistoryOrder(**order_dict))

    return result


# Get history deals
@mcp.tool()
def history_deals_get(
    symbol: str | None = None,
    group: str | None = None,
    ticket: int | None = None,
    position: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[Deal]:
    """
    Get deals from history within the specified date range.

    Args:
        symbol: Symbol name
        group: Filter for arranging a group of deals
        ticket: Deal ticket
        position: Position ticket
        from_date: Start date for deal retrieval
        to_date: End date for deal retrieval

    Returns:
        List[Deal]: List of historical deals.
    """
    request = {}
    if symbol is not None:
        request["symbol"] = symbol
    if group is not None:
        request["group"] = group
    if ticket is not None:
        request["ticket"] = ticket
    if position is not None:
        request["position"] = position
    if from_date is not None:
        request["from"] = from_date
    if to_date is not None:
        request["to"] = to_date

    # Get history deals
    if request:
        deals = mt5.history_deals_get(**request)
    else:
        deals = mt5.history_deals_get()

    if deals is None:
        logger.error(f"Failed to get history deals, error code: {mt5.last_error()}")
        return []

    result = []
    for deal in deals:
        # Convert named tuple to dictionary
        deal_dict = deal._asdict()
        result.append(Deal(**deal_dict))

    return result


# Resource for order types
@mcp.resource("mt5://order_types")
def get_order_types() -> str:
    """
    Get information about order types in MetaTrader 5.

    Returns:
        str: Information about order types.
    """
    order_types = {
        "ORDER_TYPE_BUY": mt5.ORDER_TYPE_BUY,
        "ORDER_TYPE_SELL": mt5.ORDER_TYPE_SELL,
        "ORDER_TYPE_BUY_LIMIT": mt5.ORDER_TYPE_BUY_LIMIT,
        "ORDER_TYPE_SELL_LIMIT": mt5.ORDER_TYPE_SELL_LIMIT,
        "ORDER_TYPE_BUY_STOP": mt5.ORDER_TYPE_BUY_STOP,
        "ORDER_TYPE_SELL_STOP": mt5.ORDER_TYPE_SELL_STOP,
        "ORDER_TYPE_BUY_STOP_LIMIT": mt5.ORDER_TYPE_BUY_STOP_LIMIT,
        "ORDER_TYPE_SELL_STOP_LIMIT": mt5.ORDER_TYPE_SELL_STOP_LIMIT,
        "ORDER_TYPE_CLOSE_BY": mt5.ORDER_TYPE_CLOSE_BY,
    }

    result = "Available order types in MetaTrader 5:\n\n"
    for name, value in order_types.items():
        result += f"{name}: {value}\n"

    return result


# Resource for order filling types
@mcp.resource("mt5://order_filling_types")
def get_order_filling_types() -> str:
    """
    Get information about order filling types in MetaTrader 5.

    Returns:
        str: Information about order filling types.
    """
    filling_types = {
        "ORDER_FILLING_FOK": mt5.ORDER_FILLING_FOK,
        "ORDER_FILLING_IOC": mt5.ORDER_FILLING_IOC,
        "ORDER_FILLING_RETURN": mt5.ORDER_FILLING_RETURN,
    }

    result = "Available order filling types in MetaTrader 5:\n\n"
    for name, value in filling_types.items():
        result += f"{name}: {value}\n"

    return result


# Resource for order time types
@mcp.resource("mt5://order_time_types")
def get_order_time_types() -> str:
    """
    Get information about order time types in MetaTrader 5.

    Returns:
        str: Information about order time types.
    """
    time_types = {
        "ORDER_TIME_GTC": mt5.ORDER_TIME_GTC,
        "ORDER_TIME_DAY": mt5.ORDER_TIME_DAY,
        "ORDER_TIME_SPECIFIED": mt5.ORDER_TIME_SPECIFIED,
        "ORDER_TIME_SPECIFIED_DAY": mt5.ORDER_TIME_SPECIFIED_DAY,
    }

    result = "Available order time types in MetaTrader 5:\n\n"
    for name, value in time_types.items():
        result += f"{name}: {value}\n"

    return result


# Resource for trade request actions
@mcp.resource("mt5://trade_actions")
def get_trade_actions() -> str:
    """
    Get information about trade request actions in MetaTrader 5.

    Returns:
        str: Information about trade request actions.
    """
    actions = {
        "TRADE_ACTION_DEAL": mt5.TRADE_ACTION_DEAL,
        "TRADE_ACTION_PENDING": mt5.TRADE_ACTION_PENDING,
        "TRADE_ACTION_SLTP": mt5.TRADE_ACTION_SLTP,
        "TRADE_ACTION_MODIFY": mt5.TRADE_ACTION_MODIFY,
        "TRADE_ACTION_REMOVE": mt5.TRADE_ACTION_REMOVE,
        "TRADE_ACTION_CLOSE_BY": mt5.TRADE_ACTION_CLOSE_BY,
    }

    result = "Available trade request actions in MetaTrader 5:\n\n"
    for name, value in actions.items():
        result += f"{name}: {value}\n"

    return result
