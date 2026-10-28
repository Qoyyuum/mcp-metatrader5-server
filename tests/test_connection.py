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
            result = await client.call_tool(
                "initialize", {"path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe"}
            )

        assert result.data is True
        mock_mt5.initialize.assert_called_once()

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


@pytest.mark.unit
class TestEnvCredentials:
    """Test the environment variable fallback for initialize() and login()."""

    @pytest.fixture(autouse=True)
    def clean_env(self, monkeypatch):
        for name in ("MT5_PATH", "MT5_LOGIN", "MT5_USERNAME", "MT5_PASSWORD", "MT5_SERVER"):
            monkeypatch.delenv(name, raising=False)

    @patch("mcp_mt5.main.mt5")
    async def test_login_from_env(self, mock_mt5, monkeypatch):
        """login() with no arguments uses MT5_LOGIN, MT5_PASSWORD and MT5_SERVER."""
        monkeypatch.setenv("MT5_LOGIN", "123456")
        monkeypatch.setenv("MT5_PASSWORD", "env_secret")
        monkeypatch.setenv("MT5_SERVER", "EnvServer")
        mock_mt5.login.return_value = True

        async with Client(mcp) as client:
            result = await client.call_tool("login", {})

        assert result.data is True
        mock_mt5.login.assert_called_once_with(
            login=123456, password="env_secret", server="EnvServer"
        )

    @patch("mcp_mt5.main.mt5")
    async def test_login_username_alias(self, mock_mt5, monkeypatch):
        """MT5_USERNAME is accepted as the account number."""
        monkeypatch.setenv("MT5_USERNAME", "654321")
        monkeypatch.setenv("MT5_PASSWORD", "env_secret")
        monkeypatch.setenv("MT5_SERVER", "EnvServer")
        mock_mt5.login.return_value = True

        async with Client(mcp) as client:
            result = await client.call_tool("login", {})

        assert result.data is True
        mock_mt5.login.assert_called_once_with(
            login=654321, password="env_secret", server="EnvServer"
        )

    @patch("mcp_mt5.main.mt5")
    async def test_explicit_args_override_env(self, mock_mt5, monkeypatch):
        """Explicit arguments win over the environment."""
        monkeypatch.setenv("MT5_LOGIN", "123456")
        monkeypatch.setenv("MT5_PASSWORD", "env_secret")
        monkeypatch.setenv("MT5_SERVER", "EnvServer")
        mock_mt5.login.return_value = True

        async with Client(mcp) as client:
            result = await client.call_tool("login", {"login": 999, "server": "ArgServer"})

        assert result.data is True
        mock_mt5.login.assert_called_once_with(login=999, password="env_secret", server="ArgServer")

    @patch("mcp_mt5.main.mt5")
    async def test_login_missing_credentials(self, mock_mt5):
        """A clear error names the missing settings when nothing is configured."""
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="Missing MT5 credentials"):
                await client.call_tool("login", {})

        mock_mt5.login.assert_not_called()

    @patch("mcp_mt5.main.mt5")
    async def test_login_error_does_not_leak_password(self, mock_mt5, monkeypatch):
        """The password is masked if the MT5 library echoes it in an exception."""
        monkeypatch.setenv("MT5_LOGIN", "123456")
        monkeypatch.setenv("MT5_PASSWORD", "env_secret")
        monkeypatch.setenv("MT5_SERVER", "EnvServer")
        mock_mt5.login.side_effect = RuntimeError("bad password env_secret")

        async with Client(mcp) as client:
            with pytest.raises(Exception) as exc_info:
                await client.call_tool("login", {})

        assert "env_secret" not in str(exc_info.value)
        assert "***" in str(exc_info.value)

    @patch("mcp_mt5.main.mt5")
    async def test_login_error_traceback_does_not_leak_password(
        self, mock_mt5, monkeypatch, caplog
    ):
        """The original exception is not chained, so a logged traceback cannot show the password either."""
        monkeypatch.setenv("MT5_LOGIN", "123456")
        monkeypatch.setenv("MT5_PASSWORD", "env_secret")
        monkeypatch.setenv("MT5_SERVER", "EnvServer")
        mock_mt5.login.side_effect = RuntimeError("bad password env_secret")

        with caplog.at_level("DEBUG"):
            async with Client(mcp) as client:
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool("login", {})

        assert "env_secret" not in str(exc_info.value)
        assert "env_secret" not in caplog.text

    @patch("mcp_mt5.main.mt5")
    async def test_initialize_path_from_env(self, mock_mt5, monkeypatch):
        """initialize() with no arguments uses MT5_PATH."""
        monkeypatch.setenv("MT5_PATH", "D:\\MT5\\terminal64.exe")
        mock_mt5.initialize.return_value = True

        async with Client(mcp) as client:
            result = await client.call_tool("initialize", {})

        assert result.data is True
        mock_mt5.initialize.assert_called_once_with(path="D:\\MT5\\terminal64.exe")

    @patch("mcp_mt5.main.mt5")
    async def test_initialize_without_path(self, mock_mt5):
        """initialize() with no path and no MT5_PATH lets MetaTrader5 find the terminal."""
        mock_mt5.initialize.return_value = True

        async with Client(mcp) as client:
            result = await client.call_tool("initialize", {})

        assert result.data is True
        mock_mt5.initialize.assert_called_once_with()
