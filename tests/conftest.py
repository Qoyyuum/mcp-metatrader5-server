"""Pytest configuration and fixtures for MCP MT5 tests."""

import sys
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def mock_mt5(monkeypatch):
    """Mock MetaTrader5 module for unit tests."""
    mock = MagicMock()

    # Patch the MetaTrader5 module in sys.modules
    monkeypatch.setitem(sys.modules, "MetaTrader5", mock)

    # Also patch the mt5 import in the main module
    monkeypatch.setattr("mcp_mt5.main.mt5", mock, raising=False)

    # Mock common MT5 functions
    mock.initialize.return_value = True
    mock.shutdown.return_value = None
    mock.login.return_value = True
    mock.last_error.return_value = (0, "Success")
    mock.version.return_value = (5, 0, 5260)

    # Mock account info
    mock_account = Mock()
    mock_account._asdict.return_value = {
        "login": 123456,
        "balance": 10000.0,
        "equity": 10000.0,
        "margin": 0.0,
        "margin_free": 10000.0,
        "margin_level": 0.0,
        "profit": 0.0,
        "currency": "USD",
        "leverage": 100,
        "name": "Test Account",
        "server": "TestServer",
        "trade_mode": 0,
        "limit_orders": 200,
        "margin_so_mode": 0,
        "trade_allowed": True,
        "trade_expert": True,
        "margin_mode": 0,
        "currency_digits": 2,
        "fifo_close": False,
        "credit": 0.0,
        "margin_so_call": 50.0,
        "margin_so_so": 30.0,
        "margin_initial": 0.0,
        "margin_maintenance": 0.0,
        "assets": 0.0,
        "liabilities": 0.0,
        "commission_blocked": 0.0,
    }
    mock.account_info.return_value = mock_account

    # Mock terminal info
    mock_terminal = Mock()
    mock_terminal._asdict.return_value = {
        "community_account": False,
        "community_connection": False,
        "connected": True,
        "dlls_allowed": True,
        "trade_allowed": True,
        "tradeapi_disabled": False,
        "email_enabled": False,
        "ftp_enabled": False,
        "notifications_enabled": False,
        "mqid": False,
        "build": 3802,
        "maxbars": 100000,
        "codepage": 1252,
        "ping_last": 10,
        "community_balance": 0.0,
        "retransmission": 0.0,
        "company": "Test Company",
        "name": "Test Terminal",
        "language": "English",
        "path": "C:\\Program Files\\MetaTrader 5",
        "data_path": "C:\\Users\\Test\\AppData\\Roaming\\MetaQuotes\\Terminal",
        "commondata_path": "C:\\Users\\Test\\AppData\\Roaming\\MetaQuotes\\Common",
    }
    mock.terminal_info.return_value = mock_terminal

    # Mock timeframe constants
    mock.TIMEFRAME_M1 = 1
    mock.TIMEFRAME_M2 = 2
    mock.TIMEFRAME_M3 = 3
    mock.TIMEFRAME_M4 = 4
    mock.TIMEFRAME_M5 = 5
    mock.TIMEFRAME_M6 = 6
    mock.TIMEFRAME_M10 = 10
    mock.TIMEFRAME_M12 = 12
    mock.TIMEFRAME_M15 = 15
    mock.TIMEFRAME_M20 = 20
    mock.TIMEFRAME_M30 = 30
    mock.TIMEFRAME_H1 = 16385
    mock.TIMEFRAME_H2 = 16386
    mock.TIMEFRAME_H3 = 16387
    mock.TIMEFRAME_H4 = 16388
    mock.TIMEFRAME_H6 = 16390
    mock.TIMEFRAME_H8 = 16392
    mock.TIMEFRAME_H12 = 16396
    mock.TIMEFRAME_D1 = 16408
    mock.TIMEFRAME_W1 = 32769
    mock.TIMEFRAME_MN1 = 49153

    # Mock tick flags
    mock.COPY_TICKS_ALL = -1
    mock.COPY_TICKS_INFO = 1
    mock.COPY_TICKS_TRADE = 2

    # Mock order types
    mock.ORDER_TYPE_BUY = 0
    mock.ORDER_TYPE_SELL = 1
    mock.ORDER_TYPE_BUY_LIMIT = 2
    mock.ORDER_TYPE_SELL_LIMIT = 3
    mock.ORDER_TYPE_BUY_STOP = 4
    mock.ORDER_TYPE_SELL_STOP = 5
    mock.ORDER_TYPE_BUY_STOP_LIMIT = 6
    mock.ORDER_TYPE_SELL_STOP_LIMIT = 7
    mock.ORDER_TYPE_CLOSE_BY = 8

    # Mock filling types
    mock.ORDER_FILLING_FOK = 0
    mock.ORDER_FILLING_IOC = 1
    mock.ORDER_FILLING_RETURN = 2

    # Mock time types
    mock.ORDER_TIME_GTC = 0
    mock.ORDER_TIME_DAY = 1
    mock.ORDER_TIME_SPECIFIED = 2
    mock.ORDER_TIME_SPECIFIED_DAY = 3

    # Mock trade actions
    mock.TRADE_ACTION_DEAL = 1
    mock.TRADE_ACTION_PENDING = 5
    mock.TRADE_ACTION_SLTP = 6
    mock.TRADE_ACTION_MODIFY = 7
    mock.TRADE_ACTION_REMOVE = 8
    mock.TRADE_ACTION_CLOSE_BY = 10

    # Mock trade retcodes
    mock.TRADE_RETCODE_REQUOTE = 10004
    mock.TRADE_RETCODE_REJECT = 10006
    mock.TRADE_RETCODE_CANCEL = 10007
    mock.TRADE_RETCODE_PLACED = 10008
    mock.TRADE_RETCODE_DONE = 10009
    mock.TRADE_RETCODE_DONE_PARTIAL = 10010
    mock.TRADE_RETCODE_ERROR = 10011
    mock.TRADE_RETCODE_TIMEOUT = 10012
    mock.TRADE_RETCODE_INVALID = 10013
    mock.TRADE_RETCODE_INVALID_VOLUME = 10014
    mock.TRADE_RETCODE_INVALID_PRICE = 10015
    mock.TRADE_RETCODE_INVALID_STOPS = 10016
    mock.TRADE_RETCODE_TRADE_DISABLED = 10017
    mock.TRADE_RETCODE_MARKET_CLOSED = 10018
    mock.TRADE_RETCODE_NO_MONEY = 10019
    mock.TRADE_RETCODE_PRICE_CHANGED = 10020
    mock.TRADE_RETCODE_PRICE_OFF = 10021
    mock.TRADE_RETCODE_INVALID_EXPIRATION = 10022
    mock.TRADE_RETCODE_ORDER_CHANGED = 10023
    mock.TRADE_RETCODE_TOO_MANY_REQUESTS = 10024
    mock.TRADE_RETCODE_NO_CHANGES = 10025
    mock.TRADE_RETCODE_SERVER_DISABLES_AT = 10026
    mock.TRADE_RETCODE_CLIENT_DISABLES_AT = 10027
    mock.TRADE_RETCODE_LOCKED = 10028
    mock.TRADE_RETCODE_FROZEN = 10029
    mock.TRADE_RETCODE_INVALID_FILL = 10030

    # Mock error codes
    mock.RES_S_OK = 1
    mock.RES_E_FAIL = -1
    mock.RES_E_INVALID_PARAMS = -2
    mock.RES_E_NO_MEMORY = -3
    mock.RES_E_NOT_FOUND = -4
    mock.RES_E_INVALID_VERSION = -5
    mock.RES_E_AUTH_FAILED = -6
    mock.RES_E_UNSUPPORTED = -7
    mock.RES_E_AUTO_TRADING_DISABLED = -8
    mock.RES_E_INTERNAL_FAIL = -10000
    mock.RES_E_DONE = -10001
    mock.RES_E_CANCELED = -10002

    return mock


@pytest.fixture
def sample_symbol_info():
    """Sample symbol information for testing."""
    return {
        "name": "EURUSD",
        "description": "Euro vs US Dollar",
        "path": "Forex\\EURUSD",
        "digits": 5,
        "spread": 2,
        "bid": 1.10000,
        "ask": 1.10002,
        "point": 0.00001,
        "tick_value": 1.0,
        "tick_size": 0.00001,
        "contract_size": 100000.0,
        "volume_min": 0.01,
        "volume_max": 500.0,
        "volume_step": 0.01,
    }


@pytest.fixture
def sample_tick_data():
    """Sample tick data for testing."""
    return {
        "time": 1609459200,
        "bid": 1.10000,
        "ask": 1.10002,
        "last": 1.10001,
        "volume": 100,
        "time_msc": 1609459200000,
        "flags": 6,
        "volume_real": 1.0,
    }


@pytest.fixture
def sample_rate_data():
    """Sample rate/bar data for testing."""
    return {
        "time": 1609459200,
        "open": 1.10000,
        "high": 1.10050,
        "low": 1.09950,
        "close": 1.10020,
        "tick_volume": 1000,
        "spread": 2,
        "real_volume": 100.0,
    }
