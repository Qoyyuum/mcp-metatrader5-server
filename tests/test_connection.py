"""Unit tests for MT5 connection management."""

from unittest.mock import patch

import pytest
from fastmcp import Client

from mcp_mt5.main import mcp


@pytest.mark.unit
class TestConnectionManagement:
    """Test MT5 connection initialization and management."""

    @patch("mcp_mt5.main.mt5")
    async def test_initialize_success(self, mock_mt5):
        """Test successful MT5 initialization."""
        mock_mt5.initialize.return_value = True

        async with Client(mcp) as client:
            result = await client.call_tool("initialize", {"path": ""})

        assert result.data is True
        mock_mt5.initialize.assert_called_once_with(path="")

    @patch("mcp_mt5.main.mt5")
    async def test_initialize_default_path(self, mock_mt5):
        """Test initialize defaults to MT5 auto-detection."""
        mock_mt5.initialize.return_value = True

        async with Client(mcp) as client:
            result = await client.call_tool("initialize", {})

        assert result.data is True
        mock_mt5.initialize.assert_called_once_with(path="")

    @patch("mcp_mt5.main.mt5")
    async def test_initialize_failure(self, mock_mt5):
        """Test failed MT5 initialization."""
        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (1, "Initialization failed")

        async with Client(mcp) as client:
            result = await client.call_tool(
                "initialize", {"path": "C:\\Invalid\\Path\\terminal64.exe"}
            )

        assert result.data is False
        mock_mt5.initialize.assert_called_once()
        mock_mt5.last_error.assert_called_once()

    @patch("mcp_mt5.main.mt5")
    async def test_shutdown(self, mock_mt5):
        """Test MT5 shutdown."""
        async with Client(mcp) as client:
            result = await client.call_tool("shutdown", {})

        assert result.data is True
        mock_mt5.shutdown.assert_called_once()

    @patch("mcp_mt5.main.mt5")
    async def test_login_success(self, mock_mt5):
        """Test successful login."""
        mock_mt5.login.return_value = True

        async with Client(mcp) as client:
            result = await client.call_tool(
                "login", {"login": 123456, "password": "test_pass", "server": "TestServer"}
            )

        assert result.data is True
        mock_mt5.login.assert_called_once_with(
            login=123456, password="test_pass", server="TestServer"
        )

    @patch("mcp_mt5.main.mt5")
    async def test_login_failure(self, mock_mt5):
        """Test failed login."""
        mock_mt5.login.return_value = False
        mock_mt5.last_error.return_value = (2, "Invalid credentials")

        async with Client(mcp) as client:
            result = await client.call_tool(
                "login", {"login": 123456, "password": "wrong_pass", "server": "TestServer"}
            )

        assert result.data is False
        mock_mt5.login.assert_called_once()
        mock_mt5.last_error.assert_called_once()

    @patch("mcp_mt5.main.mt5")
    async def test_get_version(self, mock_mt5):
        """Test getting MT5 version."""
        mock_mt5.version.return_value = (5, 0, 5260)

        async with Client(mcp) as client:
            result = await client.call_tool("get_version", {})

        assert result.data == {"version": 5, "build": 0, "date": 5260}
        mock_mt5.version.assert_called_once()

    @patch("mcp_mt5.main.mt5")
    async def test_get_version_failure(self, mock_mt5):
        """Test get_version when MT5 returns None."""
        mock_mt5.version.return_value = None
        mock_mt5.last_error.return_value = (3, "Not connected")

        async with Client(mcp) as client:
            with pytest.raises(Exception, match="Failed to get version"):
                await client.call_tool("get_version", {})

        mock_mt5.version.assert_called_once()
        mock_mt5.last_error.assert_called_once()


@pytest.mark.unit
class TestConnectionParameters:
    """Test connection parameter validation."""

    @patch("mcp_mt5.main.mt5")
    async def test_initialize_with_various_paths(self, mock_mt5):
        """Test initialize with different path formats."""
        mock_mt5.initialize.return_value = True

        paths = [
            "",
            "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
            "C:/Program Files/MetaTrader 5/terminal64.exe",
            "D:\\MT5\\terminal64.exe",
        ]

        async with Client(mcp) as client:
            for path in paths:
                result = await client.call_tool("initialize", {"path": path})
                assert result.data is True

    @patch("mcp_mt5.main.mt5")
    async def test_login_with_different_servers(self, mock_mt5):
        """Test login with different server names."""
        mock_mt5.login.return_value = True

        servers = [
            "MetaQuotes-Demo",
            "Broker-Live",
            "TestServer-01",
        ]

        async with Client(mcp) as client:
            for server in servers:
                result = await client.call_tool(
                    "login", {"login": 123456, "password": "pass", "server": server}
                )
                assert result.data is True
