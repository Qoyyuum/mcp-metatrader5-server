"""A drop-in, ``MetaTrader5``-shaped adapter backed by the TickerAll hosted API.

This module mirrors the subset of the ``MetaTrader5`` Python package that
``main.py`` uses - the same function names, the same ``._asdict()`` return
shape, and the same ``TIMEFRAME_*`` / ``ORDER_*`` / ``TRADE_ACTION_*`` /
``TRADE_RETCODE_*`` integer constants - but serves every call from the hosted
TickerAll MT5 API (https://tickerall.com) instead of a local terminal. That
lets the server run on any OS, in a container, with no MetaTrader 5 installed.

It is selected transparently by :func:`mcp_mt5.backend.get_backend` when
``TICKERALL_API_KEY`` is set; upstream/local behaviour is untouched otherwise.

Configuration (environment variables):

* ``TICKERALL_API_KEY``     - required. Your TickerAll API key (``cf_api_...``).
* ``TICKERALL_ACCOUNT_ID``  - optional. If your key has several connected
  accounts, set this to target one directly; otherwise the account is resolved
  from your key (or from the one you ``login()`` with).

Connecting: call ``login(login=..., password=..., server=...)`` and the server
connects and warms that account for you - no separate step is needed. If your
key already has a single account, it is used automatically without ``login()``.

Honest limitations (never faked - see the raising stubs below):

* ``copy_ticks_*`` (historical *raw ticks*): not *yet* served by the hosted API.
  Use ``copy_rates_*`` for OHLC bars or the live tick stream for real-time ticks.
* ``order_check`` (broker dry-run): the hosted API validates broker-side on
  send, so this returns a clearly-labelled pass-through rather than a fake
  margin projection.
* Hosted OHLC covers these timeframes: M1, M5, M15, M30, H1, H4, D1, W1, MN1.
* The broker account number is returned masked (privacy); only trailing digits
  are visible in ``account_info().login``.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from fnmatch import fnmatch
from typing import Any

logger = logging.getLogger(__name__)

try:
    from tickerall import Tickerall
    from tickerall import errors as ta_errors
except ImportError as exc:  # pragma: no cover - guidance path
    raise ImportError(
        "TICKERALL_API_KEY is set but the 'tickerall' package is not installed. "
        "Install it with:  pip install tickerall   (or: pip install "
        "mcp-metatrader5-server[tickerall])"
    ) from exc

# Optional dependency for remembering accounts (encrypted, machine-bound - see
# the credential-store section in _Provider). If unavailable, the provider
# simply does not remember accounts (login is required each session).
try:
    from cryptography.fernet import Fernet, InvalidToken

    _HAS_CRYPTO = True
except ImportError:  # pragma: no cover
    _HAS_CRYPTO = False


# ---------------------------------------------------------------------------
# MetaTrader 5 integer constants (public MQL5 values). main.py references many
# of these at *import time* (e.g. the module-level timeframe map, the
# copy_ticks_* default args, and the OrderRequest validators), so they must all
# exist here with their real values.
# ---------------------------------------------------------------------------

# Timeframes (minutes for M*, packed values for H*/D1/W1/MN1)
TIMEFRAME_M1 = 1
TIMEFRAME_M2 = 2
TIMEFRAME_M3 = 3
TIMEFRAME_M4 = 4
TIMEFRAME_M5 = 5
TIMEFRAME_M6 = 6
TIMEFRAME_M10 = 10
TIMEFRAME_M12 = 12
TIMEFRAME_M15 = 15
TIMEFRAME_M20 = 20
TIMEFRAME_M30 = 30
TIMEFRAME_H1 = 16385
TIMEFRAME_H2 = 16386
TIMEFRAME_H3 = 16387
TIMEFRAME_H4 = 16388
TIMEFRAME_H6 = 16390
TIMEFRAME_H8 = 16392
TIMEFRAME_H12 = 16396
TIMEFRAME_D1 = 16408
TIMEFRAME_W1 = 32769
TIMEFRAME_MN1 = 49153

# Trade actions
TRADE_ACTION_DEAL = 1
TRADE_ACTION_PENDING = 5
TRADE_ACTION_SLTP = 6
TRADE_ACTION_MODIFY = 7
TRADE_ACTION_REMOVE = 8
TRADE_ACTION_CLOSE_BY = 10

# Order types
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5
ORDER_TYPE_BUY_STOP_LIMIT = 6
ORDER_TYPE_SELL_STOP_LIMIT = 7
ORDER_TYPE_CLOSE_BY = 8

# Order filling / time
ORDER_FILLING_FOK = 0
ORDER_FILLING_IOC = 1
ORDER_FILLING_RETURN = 2
ORDER_TIME_GTC = 0
ORDER_TIME_DAY = 1
ORDER_TIME_SPECIFIED = 2
ORDER_TIME_SPECIFIED_DAY = 3

# Tick copy flags
COPY_TICKS_ALL = -1
COPY_TICKS_INFO = 1
COPY_TICKS_TRADE = 2

# last_error() result codes
RES_S_OK = 1
RES_E_FAIL = -1
RES_E_INVALID_PARAMS = -2
RES_E_NO_MEMORY = -3
RES_E_NOT_FOUND = -4
RES_E_INVALID_VERSION = -5
RES_E_AUTH_FAILED = -6
RES_E_UNSUPPORTED = -7
RES_E_AUTO_TRADING_DISABLED = -8
RES_E_INTERNAL_FAIL = -10000

# Trade return codes
TRADE_RETCODE_REQUOTE = 10004
TRADE_RETCODE_REJECT = 10006
TRADE_RETCODE_CANCEL = 10007
TRADE_RETCODE_PLACED = 10008
TRADE_RETCODE_DONE = 10009
TRADE_RETCODE_DONE_PARTIAL = 10010
TRADE_RETCODE_ERROR = 10011
TRADE_RETCODE_TIMEOUT = 10012
TRADE_RETCODE_INVALID = 10013
TRADE_RETCODE_INVALID_VOLUME = 10014
TRADE_RETCODE_INVALID_PRICE = 10015
TRADE_RETCODE_INVALID_STOPS = 10016
TRADE_RETCODE_TRADE_DISABLED = 10017
TRADE_RETCODE_MARKET_CLOSED = 10018
TRADE_RETCODE_NO_MONEY = 10019
TRADE_RETCODE_PRICE_CHANGED = 10020
TRADE_RETCODE_PRICE_OFF = 10021
TRADE_RETCODE_INVALID_EXPIRATION = 10022
TRADE_RETCODE_ORDER_CHANGED = 10023
TRADE_RETCODE_TOO_MANY_REQUESTS = 10024
TRADE_RETCODE_NO_CHANGES = 10025
TRADE_RETCODE_SERVER_DISABLES_AT = 10026
TRADE_RETCODE_CLIENT_DISABLES_AT = 10027
TRADE_RETCODE_LOCKED = 10028
TRADE_RETCODE_FROZEN = 10029
TRADE_RETCODE_INVALID_FILL = 10030

# MT5 timeframe constant -> hosted TickerAll timeframe string
_CONST_TO_TF = {
    TIMEFRAME_M1: "M1",
    TIMEFRAME_M5: "M5",
    TIMEFRAME_M15: "M15",
    TIMEFRAME_M30: "M30",
    TIMEFRAME_H1: "H1",
    TIMEFRAME_H4: "H4",
    TIMEFRAME_D1: "D1",
    TIMEFRAME_W1: "W1",
    TIMEFRAME_MN1: "MN1",
}

# Minutes per hosted timeframe, used to size a date/range history fetch (the
# hosted API is count-based, so we estimate how many recent bars reach the
# requested start).
_CONST_TO_MINUTES = {
    TIMEFRAME_M1: 1,
    TIMEFRAME_M5: 5,
    TIMEFRAME_M15: 15,
    TIMEFRAME_M30: 30,
    TIMEFRAME_H1: 60,
    TIMEFRAME_H4: 240,
    TIMEFRAME_D1: 1440,
    TIMEFRAME_W1: 10080,
    TIMEFRAME_MN1: 43200,
}
# Upper bound on bars fetched for one date/range query; beyond this the request
# is reported as deeper than the available history rather than silently partial.
_MAX_RATES_FETCH = 20000


class _Struct:
    """Mimics MetaTrader5's namedtuple returns: attribute access + ``_asdict()``."""

    def __init__(self, **fields: Any) -> None:
        self.__dict__.update(fields)

    def _asdict(self) -> dict[str, Any]:
        return dict(self.__dict__)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"_Struct({self.__dict__!r})"


def _iso_to_epoch(value: Any) -> int:
    """ISO-8601 string (or epoch number) -> integer epoch seconds. 0 if absent."""
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        # Broker timestamps are UTC; treat a naive one as UTC rather than local.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return int(dt.timestamp())
    except (ValueError, TypeError):
        return 0


class _Provider:
    """Holds the TickerAll client + resolved account and maps MT5 calls to it."""

    def __init__(self) -> None:
        self._client: Tickerall | None = None
        self._account_id: str | None = None
        self._is_demo: bool | None = None
        self._server: str = ""
        self._last_error: tuple[int, str] = (RES_S_OK, "Success")
        self._stream = None
        self._subscribed: set[str] = set()
        self._symbol_specs: dict[str, Any] | None = None

    # -- lifecycle ---------------------------------------------------------
    def _ensure_client(self) -> Tickerall:
        if self._client is None:
            self._client = Tickerall(api_key=os.getenv("TICKERALL_API_KEY"))
        return self._client

    def _resolve_account(self) -> str:
        if self._account_id:
            return self._account_id
        client = self._ensure_client()
        env_id = os.getenv("TICKERALL_ACCOUNT_ID")
        if env_id:
            self._account_id = env_id
        else:
            accounts = client.accounts.list()
            if len(accounts) == 1:
                self._account_id = accounts[0].id
            elif not accounts:
                # Nothing connected - reconnect a single remembered account, if any.
                stored = self._load_stored()
                if len(stored) == 1:
                    self._reconnect_stored(next(iter(stored)))
                    return self._account_id
                raise ValueError(
                    "No account is selected yet. Call login(login, password, server) "
                    "to connect one."
                )
            else:
                choices = ", ".join(f"{a.id} ({a.server})" for a in accounts)
                raise ValueError(
                    "This API key has several connected accounts. Call list_accounts() "
                    "to see them, then use_account(account_id) to pick one - or "
                    f"login(...) to add a new one. Available: {choices}"
                )
        # Cache demo status + server. If the account has gone cold and we
        # remember it, transparently re-warm it (TickerAll is stateless).
        detail = client.accounts.get(self._account_id)
        if detail.account is None and self._reconnect_stored(self._account_id):
            detail = client.accounts.get(self._account_id)
        self._is_demo = detail.is_demo
        self._server = detail.server
        return self._account_id

    def initialize(self, path: str | None = None) -> bool:
        try:
            client = self._ensure_client()
            # Validate the API key without requiring a specific account: the
            # account is resolved later (via login(), or a single connected
            # account is used automatically), so the login-first flow works even
            # when the key has zero or several connected accounts.
            client.accounts.list()
            self._ok()
            return True
        except Exception as exc:
            self._fail(RES_E_AUTH_FAILED, str(exc))
            logger.error("TickerAll initialize failed: %s", exc)
            return False

    def login(self, login: int, password: str, server: str) -> bool:
        # Connect + warm this account, make it active, and remember it so it can
        # be re-warmed later without asking again (TickerAll is stateless). An
        # explicit login always switches the active account.
        try:
            result = self._connect(server=server, account=login, password=password)
            self._store_cred(result.account_id, login, password, server, result.is_demo)
            self._ok()
            return True
        except Exception as exc:
            self._fail(RES_E_AUTH_FAILED, str(exc))
            logger.error("TickerAll login failed: %s", exc)
            return False

    def _connect(self, *, server: str, account: int, password: str):
        """Start (or re-warm) a hosted session and make that account active."""
        result = self._ensure_client().sessions.start(
            broker="mt5", server=server, account=account, password=password
        )
        self._reset_account_caches()
        self._account_id = result.account_id
        self._is_demo = result.is_demo
        self._server = server
        return result

    def _reset_account_caches(self) -> None:
        """Drop per-account cached state when the active account changes."""
        self._symbol_specs = None
        self._subscribed = set()
        if self._stream is not None:
            with contextlib.suppress(Exception):
                self._stream.close()
            self._stream = None

    def list_accounts(self) -> list[dict[str, Any]]:
        """Every broker account connected to this API key (for the AI to pick)."""
        client = self._ensure_client()
        out: list[dict[str, Any]] = []
        for a in client.accounts.list():
            out.append(
                {
                    "account_id": a.id,
                    "server": a.server,
                    "number": a.account_number,
                    "is_demo": a.is_demo,
                    "connected": a.status == "CONNECTED",
                    "hot": a.hot,
                    "active": a.id == self._account_id,
                }
            )
        return out

    def use_account(self, account_id: str) -> dict[str, Any]:
        """Make a connected account active (no password needed).

        Re-warms it from remembered credentials if it has gone cold or dropped.
        """
        client = self._ensure_client()
        accounts = {a.id: a for a in client.accounts.list()}
        account = accounts.get(account_id)
        if account is None:
            # Not connected right now - reconnect it if we remember its creds.
            if self._reconnect_stored(account_id):
                return self._active_summary()
            raise ValueError(
                f"Account '{account_id}' is not connected to this API key. Use "
                "login(login, password, server) to connect it."
            )
        # Connected but cold: re-warm from remembered creds (else best-effort rearm).
        if not account.hot and not self._reconnect_stored(account_id):
            with contextlib.suppress(Exception):
                client.rearm(account_id)
        if account_id != self._account_id:
            self._reset_account_caches()
        self._account_id = account_id
        self._is_demo = account.is_demo
        self._server = account.server
        self._ok()
        return self._active_summary()

    def _active_summary(self) -> dict[str, Any]:
        return {
            "account_id": self._account_id,
            "server": self._server,
            "is_demo": self._is_demo,
            "active": True,
        }

    def _reconnect_stored(self, account_id: str) -> bool:
        """Reconnect account_id from remembered credentials. True if it did."""
        creds = self._load_stored().get(account_id)
        if not creds:
            return False
        self._connect(server=creds["server"], account=creds["account"], password=creds["password"])
        self._ok()
        return True

    # -- remembered accounts ----------------------------------------------
    # TickerAll is stateless and never persists broker credentials, so to avoid
    # asking the user to log in again each session the client remembers them
    # here. The store is CLIENT-SIDE ONLY, encrypted at rest with a key derived
    # from this machine (so the file is useless if copied off it), and 0600.
    # Set TICKERALL_REMEMBER_ACCOUNTS=0 to disable; delete the file to forget.
    @staticmethod
    def _creds_dir() -> str:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
        return os.path.join(base, "mcp-metatrader5-server")

    @classmethod
    def _creds_file(cls) -> str:
        return os.path.join(cls._creds_dir(), "credentials.enc")

    @staticmethod
    def _remember_enabled() -> bool:
        return _HAS_CRYPTO and os.getenv("TICKERALL_REMEMBER_ACCOUNTS", "1") != "0"

    @staticmethod
    def _machine_id() -> bytes:
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                with open(path) as f:
                    value = f.read().strip()
                if value:
                    return value.encode()
            except OSError:
                pass
        # Cross-platform fallback (macOS / Windows / containers w/o machine-id).
        import platform
        import uuid

        return f"{uuid.getnode()}:{platform.node()}".encode()

    @classmethod
    def _cipher(cls) -> Fernet:
        # Key = machine id + this user's home + a constant app tag. Binds the
        # store to (this machine, this user); recoverable on-box (inherent), but
        # useless anywhere else.
        material = (
            cls._machine_id()
            + os.path.expanduser("~").encode()
            + b"mcp-metatrader5-server/tickerall/creds/v1"
        )
        return Fernet(base64.urlsafe_b64encode(hashlib.sha256(material).digest()))

    def _load_stored(self) -> dict[str, dict[str, Any]]:
        if not _HAS_CRYPTO:
            return {}
        try:
            with open(self._creds_file(), "rb") as f:
                blob = f.read()
            if not blob:
                return {}
            data = json.loads(self._cipher().decrypt(blob))
            return data if isinstance(data, dict) else {}
        except (FileNotFoundError, OSError, InvalidToken, ValueError):
            # Missing, unreadable, corrupt, or written on another machine.
            return {}

    def _store_cred(
        self, account_id: str, account: int, password: str, server: str, is_demo: bool
    ) -> None:
        if not self._remember_enabled():
            return
        try:
            data = self._load_stored()
            data[account_id] = {
                "account": account,
                "password": password,
                "server": server,
                "is_demo": bool(is_demo),
            }
            blob = self._cipher().encrypt(json.dumps(data).encode())
            os.makedirs(self._creds_dir(), exist_ok=True)
            with contextlib.suppress(OSError):
                os.chmod(self._creds_dir(), 0o700)
            # Create with 0600 AT OPEN TIME, so there is never a window where the
            # file exists with default (looser) permissions. On Windows the mode
            # is advisory; the encryption is the real protection there.
            path = self._creds_file()
            with contextlib.suppress(FileNotFoundError):
                os.remove(path)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(blob)
        except OSError as exc:
            logger.warning("Could not remember TickerAll account: %s", exc)

    def shutdown(self) -> bool:
        try:
            if self._stream is not None:
                self._stream.close()
                self._stream = None
            if self._client is not None:
                self._client.close()
                self._client = None
        except Exception as exc:
            logger.warning("TickerAll shutdown warning: %s", exc)
        return True

    # -- error bookkeeping -------------------------------------------------
    def _ok(self) -> None:
        self._last_error = (RES_S_OK, "Success")

    def _fail(self, code: int, msg: str) -> None:
        self._last_error = (code, msg)

    def last_error(self) -> tuple[int, str]:
        return self._last_error

    # -- account / terminal ------------------------------------------------
    def account_info(self) -> _Struct | None:
        try:
            account_id = self._resolve_account()
            detail = self._ensure_client().accounts.get(account_id)
            acc = detail.account
            if acc is None:
                self._fail(RES_E_NOT_FOUND, detail.hint or "account snapshot unavailable")
                return None
            balance = acc.balance
            # equity/margin may be *absent* (None) - distinct from a real 0.0 value.
            equity = acc.equity if acc.equity is not None else balance
            margin = acc.margin if acc.margin is not None else 0.0
            free_margin = acc.free_margin if acc.free_margin is not None else equity
            margin_level = acc.margin_level if acc.margin_level is not None else 0.0
            profit = (equity - balance) if acc.equity is not None else 0.0
            digits = "".join(ch for ch in detail.account_number if ch.isdigit())
            self._ok()
            return _Struct(
                login=int(digits) if digits else 0,
                trade_mode=0 if detail.is_demo else 2,
                leverage=acc.leverage,
                limit_orders=0,
                margin_so_mode=0,
                trade_allowed=True,
                trade_expert=True,
                margin_mode=0,
                currency_digits=2,
                fifo_close=False,
                balance=balance,
                credit=0.0,
                profit=profit,
                equity=equity,
                margin=margin,
                margin_free=free_margin,
                margin_level=margin_level,
                margin_so_call=0.0,
                margin_so_so=0.0,
                margin_initial=0.0,
                margin_maintenance=0.0,
                assets=0.0,
                liabilities=0.0,
                commission_blocked=0.0,
                name=acc.name,
                server=detail.server,
                currency=acc.currency or "",
                company=acc.broker_name or detail.broker,
            )
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll account_info failed: %s", exc)
            return None

    def terminal_info(self) -> _Struct:
        self._ok()
        return _Struct(
            community_account=False,
            community_connection=False,
            connected=True,
            dlls_allowed=False,
            trade_allowed=True,
            tradeapi_disabled=False,
            email_enabled=False,
            ftp_enabled=False,
            notifications_enabled=False,
            mqid=False,
            build=0,
            maxbars=100000,
            codepage=0,
            ping_last=0,
            community_balance=0.0,
            retransmission=0.0,
            company="TickerAll - hosted MT5 API",
            name="TickerAll Hosted Provider",
            language="English",
            path="",
            data_path="",
            commondata_path="",
            hosted=True,
            provider="tickerall",
        )

    def version(self) -> tuple[int, int, str]:
        self._ok()
        return (500, 5735, "TickerAll hosted")

    # -- symbols -----------------------------------------------------------
    def _specs(self) -> dict[str, Any]:
        if self._symbol_specs is None:
            account_id = self._resolve_account()
            specs = self._ensure_client().accounts.symbol_specs(account_id)
            self._symbol_specs = {s.name: s for s in specs}
        return self._symbol_specs

    def symbols_get(self, group: str | None = None) -> list[_Struct] | None:
        try:
            account_id = self._resolve_account()
            names = self._ensure_client().accounts.symbols(account_id)
            if group:
                names = [n for n in names if fnmatch(n, group)]
            self._ok()
            return [_Struct(name=n) for n in names]
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll symbols_get failed: %s", exc)
            return None

    def symbol_info(self, symbol: str) -> _Struct | None:
        try:
            spec = self._specs().get(symbol)
            if spec is None:
                self._fail(RES_E_NOT_FOUND, f"symbol {symbol} not found")
                return None
            bid = ask = last = None
            if self._stream is not None:
                cached = self._stream.latest_tick(symbol)
                if cached is not None:
                    bid, ask, last = cached.bid, cached.ask, cached.bid
            self._ok()
            return _Struct(
                name=spec.name,
                digits=spec.digits,
                point=spec.point,
                tick_size=spec.tick_size,
                tick_value=spec.tick_value,
                contract_size=spec.contract_size,
                volume_min=spec.volume_min,
                volume_max=spec.volume_max,
                volume_step=spec.volume_step,
                trade_mode=spec.trade_mode,
                # Report IOC filling so main._get_supported_filling_mode picks IOC.
                filling_mode=2,
                trade_exemode=2,
                bid=bid,
                ask=ask,
                last=last,
            )
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll symbol_info failed: %s", exc)
            return None

    def _ensure_stream(self):
        if self._stream is None or not self._stream.is_connected():
            client = self._ensure_client()
            self._stream = client.stream.connect(timeout=15.0)
            self._subscribed = set()
        return self._stream

    def symbol_info_tick(self, symbol: str) -> _Struct | None:
        try:
            account_id = self._resolve_account()
            stream = self._ensure_stream()
            if symbol not in self._subscribed:
                stream.subscribe_ticks(account_id, [symbol])
                self._subscribed.add(symbol)
            tick = None
            try:
                tick = stream.wait_for_tick(symbol, account_id=account_id, timeout=6.0)
            except Exception:
                tick = stream.latest_tick(symbol)
            if tick is not None:
                epoch = _iso_to_epoch(tick.timestamp)
                self._ok()
                return _Struct(
                    time=epoch,
                    bid=tick.bid,
                    ask=tick.ask,
                    last=tick.bid,
                    volume=0,
                    time_msc=epoch * 1000,
                    flags=0,
                    volume_real=0.0,
                )
            # Fallback: last M1 bar (documented ~1-minute-delayed quote).
            bars = self._ensure_client().candles.get(
                account_id, symbol=symbol, count=1, timeframe="M1"
            )
            if bars:
                bar = bars[-1]
                epoch = _iso_to_epoch(bar.timestamp)
                self._ok()
                return _Struct(
                    time=epoch,
                    bid=bar.bid or bar.close,
                    ask=bar.close,
                    last=bar.close,
                    volume=bar.tick_volume,
                    time_msc=epoch * 1000,
                    flags=0,
                    volume_real=0.0,
                )
            self._fail(RES_E_NOT_FOUND, f"no tick for {symbol}")
            return None
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll symbol_info_tick failed: %s", exc)
            return None

    def symbol_select(self, symbol: str, visible: bool = True) -> bool:
        # Hosted API auto-manages symbol availability; nothing to select.
        self._ok()
        return True

    # -- rates -------------------------------------------------------------
    def _tf(self, timeframe_const: int) -> str:
        tf = _CONST_TO_TF.get(timeframe_const)
        if tf is None:
            supported = ", ".join(_CONST_TO_TF[c] for c in sorted(_CONST_TO_TF))
            raise ValueError(
                f"Timeframe {timeframe_const} is not available via the hosted "
                f"TickerAll provider. Supported timeframes: {supported}."
            )
        return tf

    def _bars(self, symbol: str, timeframe_const: int, count: int) -> list[Any]:
        account_id = self._resolve_account()
        tf = self._tf(timeframe_const)
        bars = self._ensure_client().candles.get(
            account_id, symbol=symbol, count=count, timeframe=tf
        )
        return sorted(bars, key=lambda b: b.timestamp)

    @staticmethod
    def _bar_row(bar: Any) -> dict[str, Any]:
        return {
            "time": _iso_to_epoch(bar.timestamp),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "tick_volume": bar.tick_volume,
            "spread": int(bar.spread) if bar.spread is not None else 0,
            "real_volume": 0,
        }

    def copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ) -> list[dict[str, Any]] | None:
        try:
            bars = self._bars(symbol, timeframe, count + max(start_pos, 0))
            if start_pos > 0:
                bars = bars[: len(bars) - start_pos] if len(bars) > start_pos else []
            rows = [self._bar_row(b) for b in bars[-count:]]
            self._ok()
            return rows
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll copy_rates_from_pos failed: %s", exc)
            return None

    def copy_rates_from_date(
        self, symbol: str, timeframe: int, date_from: datetime, count: int
    ) -> list[dict[str, Any]] | None:
        try:
            frm = self._to_epoch(date_from)
            bars = self._bars(symbol, timeframe, self._span_count(timeframe, frm, None, count))
            # If the oldest bar we could fetch is still newer than date_from, the
            # available history is shallower than requested. Fail honestly rather
            # than silently returning the most recent bars instead.
            if bars and _iso_to_epoch(bars[0].timestamp) > frm:
                self._fail(RES_E_NOT_FOUND, "requested history is deeper than available")
                return None
            window = [b for b in bars if _iso_to_epoch(b.timestamp) >= frm][:count]
            self._ok()
            return [self._bar_row(b) for b in window]
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll copy_rates_from_date failed: %s", exc)
            return None

    def copy_rates_range(
        self, symbol: str, timeframe: int, date_from: datetime, date_to: datetime
    ) -> list[dict[str, Any]] | None:
        try:
            frm, to = self._to_epoch(date_from), self._to_epoch(date_to)
            bars = self._bars(symbol, timeframe, self._span_count(timeframe, frm, to, None))
            window = [b for b in bars if frm <= _iso_to_epoch(b.timestamp) <= to]
            if not window:
                # No bars in the range (or history didn't reach it): fail rather
                # than report a silent successful empty result.
                self._fail(RES_E_NOT_FOUND, "no bars available for the requested range")
                return None
            self._ok()
            return [self._bar_row(b) for b in window]
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll copy_rates_range failed: %s", exc)
            return None

    @staticmethod
    def _span_count(timeframe_const: int, frm: int, to: int | None, count: int | None) -> int:
        """Recent-bar count to fetch to (try to) reach `frm`, bounded by a cap."""
        tf_min = _CONST_TO_MINUTES.get(timeframe_const, 1)
        upper = to if to is not None else int(datetime.now(UTC).timestamp())
        span = max(1, (upper - frm) // (tf_min * 60)) + (count or 0) + 8
        return int(min(span, _MAX_RATES_FETCH))

    @staticmethod
    def _to_epoch(value: Any) -> int:
        if isinstance(value, datetime):
            dt = value if value.tzinfo else value.replace(tzinfo=UTC)
            return int(dt.timestamp())
        return _iso_to_epoch(value)

    # -- ticks (honest gap) ------------------------------------------------
    def copy_ticks_from(self, *args: Any, **kwargs: Any):
        raise ValueError(
            "Historical raw ticks are not yet available via the hosted TickerAll "
            "provider. Use copy_rates_* for OHLC bars, or get_symbol_info_tick / "
            "the live stream for real-time ticks."
        )

    copy_ticks_range = copy_ticks_from

    # -- trading -----------------------------------------------------------
    def order_send(self, request: dict[str, Any]) -> _Struct | None:
        try:
            account_id = self._resolve_account()
            client = self._ensure_client()
            orders = client.orders
            positions = client.positions
            action = request.get("action")
            symbol = request.get("symbol")
            volume = request.get("volume")
            order_type = request.get("type")
            price = request.get("price")
            sl = request.get("sl")
            tp = request.get("tp")
            comment = request.get("comment")

            if action == TRADE_ACTION_DEAL:
                if request.get("position") is not None:
                    res = positions.close(
                        account_id, ticket=int(request["position"]), volume=volume
                    )
                    return self._order_ok(
                        request,
                        retcode=TRADE_RETCODE_DONE,
                        order=res.ticket,
                        deal=res.ticket,
                        volume=res.volume,
                        price=price or 0.0,
                        comment="closed",
                    )
                side = "SELL" if order_type == ORDER_TYPE_SELL else "BUY"
                res = orders.place(
                    account_id,
                    type="market",
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    stop_loss=sl,
                    take_profit=tp,
                    comment=comment,
                )
                return self._order_ok(
                    request,
                    retcode=TRADE_RETCODE_DONE,
                    order=res.ticket,
                    deal=res.ticket,
                    volume=res.volume,
                    price=res.price or price or 0.0,
                    comment=res.comment or res.status,
                )

            if action == TRADE_ACTION_PENDING:
                hosted_type = self._pending_type(order_type)
                side = (
                    "SELL"
                    if order_type
                    in (ORDER_TYPE_SELL_LIMIT, ORDER_TYPE_SELL_STOP, ORDER_TYPE_SELL_STOP_LIMIT)
                    else "BUY"
                )
                res = orders.place(
                    account_id,
                    type=hosted_type,
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    price=price,
                    stop_loss=sl,
                    take_profit=tp,
                    comment=comment,
                )
                return self._order_ok(
                    request,
                    retcode=TRADE_RETCODE_PLACED,
                    order=res.ticket,
                    deal=0,
                    volume=res.volume,
                    price=res.price or price or 0.0,
                    comment=res.comment or res.status,
                )

            if action == TRADE_ACTION_SLTP:
                res = positions.modify(
                    account_id,
                    ticket=int(request["position"]),
                    stop_loss=sl,
                    take_profit=tp,
                )
                return self._order_ok(
                    request,
                    retcode=TRADE_RETCODE_DONE,
                    order=res.ticket,
                    deal=0,
                    volume=res.volume,
                    price=0.0,
                    comment="modified",
                )

            if action == TRADE_ACTION_MODIFY:
                res = orders.modify_pending(
                    account_id,
                    ticket=int(request["order"]),
                    price=price,
                    stop_loss=sl,
                    take_profit=tp,
                )
                return self._order_ok(
                    request,
                    retcode=TRADE_RETCODE_DONE,
                    order=res.ticket,
                    deal=0,
                    volume=0.0,
                    price=res.price or price or 0.0,
                    comment="modified",
                )

            if action == TRADE_ACTION_REMOVE:
                res = orders.cancel_pending(account_id, ticket=int(request["order"]))
                return self._order_ok(
                    request,
                    retcode=TRADE_RETCODE_DONE,
                    order=res.ticket,
                    deal=0,
                    volume=0.0,
                    price=0.0,
                    comment="cancelled",
                )

            if action == TRADE_ACTION_CLOSE_BY:
                self._fail(RES_E_UNSUPPORTED, "close-by is not supported by the hosted provider")
                return self._order_fail(
                    request,
                    TRADE_RETCODE_INVALID,
                    "close-by (TRADE_ACTION_CLOSE_BY) is not supported via the hosted TickerAll provider",
                )

            self._fail(RES_E_INVALID_PARAMS, f"unknown action {action}")
            return self._order_fail(request, TRADE_RETCODE_INVALID, f"unknown action {action}")
        except ta_errors.TickerallBrokerError as exc:
            self._fail(RES_E_FAIL, str(exc))
            return self._order_fail(request, TRADE_RETCODE_REJECT, str(exc))
        except ta_errors.TickerallValidationError as exc:
            self._fail(RES_E_INVALID_PARAMS, str(exc))
            return self._order_fail(request, TRADE_RETCODE_INVALID, str(exc))
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll order_send failed: %s", exc)
            return None

    @staticmethod
    def _pending_type(order_type: int) -> str:
        if order_type in (ORDER_TYPE_BUY_LIMIT, ORDER_TYPE_SELL_LIMIT):
            return "limit"
        if order_type in (ORDER_TYPE_BUY_STOP, ORDER_TYPE_SELL_STOP):
            return "stop"
        raise ValueError(
            "Stop-limit pending orders are not supported via the hosted TickerAll "
            "provider (supported pending types: limit, stop)."
        )

    def _order_ok(self, request, *, retcode, order, deal, volume, price, comment) -> _Struct:
        self._ok()
        return _Struct(
            retcode=retcode,
            deal=int(deal or 0),
            order=int(order or 0),
            volume=float(volume or 0.0),
            price=float(price or 0.0),
            bid=0.0,
            ask=0.0,
            comment=str(comment or ""),
            request_id=0,
            retcode_external=0,
            request=dict(request),
        )

    def _order_fail(self, request, retcode, comment) -> _Struct:
        return _Struct(
            retcode=retcode,
            deal=0,
            order=0,
            volume=0.0,
            price=0.0,
            bid=0.0,
            ask=0.0,
            comment=str(comment),
            request_id=0,
            retcode_external=0,
            request=dict(request),
        )

    def order_check(self, request: dict[str, Any]) -> _Struct:
        # No hosted dry-run: the broker validates on send. Report a clearly
        # labelled pass-through with current account figures (never a fake
        # margin projection).
        info = self.account_info()
        balance = getattr(info, "balance", 0.0) if info else 0.0
        equity = getattr(info, "equity", 0.0) if info else 0.0
        margin_free = getattr(info, "margin_free", 0.0) if info else 0.0
        self._ok()
        return _Struct(
            retcode=0,
            balance=balance,
            equity=equity,
            profit=0.0,
            margin=0.0,
            margin_free=margin_free,
            margin_level=0.0,
            comment="hosted mode: not pre-validated; the broker validates on order_send",
            request=dict(request),
        )

    # -- positions / orders ------------------------------------------------
    def positions_get(self, symbol=None, group=None, ticket=None) -> list[_Struct] | None:
        try:
            account_id = self._resolve_account()
            detail = self._ensure_client().accounts.get(account_id)
            out = []
            for p in detail.positions:
                if symbol is not None and p.symbol != symbol:
                    continue
                if group is not None and not fnmatch(p.symbol, group):
                    continue
                if ticket is not None and int(p.ticket) != int(ticket):
                    continue
                out.append(self._position_struct(p))
            self._ok()
            return out
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll positions_get failed: %s", exc)
            return None

    @staticmethod
    def _position_struct(p: Any) -> _Struct:
        epoch = _iso_to_epoch(p.open_time)
        return _Struct(
            ticket=int(p.ticket),
            time=epoch,
            time_msc=epoch * 1000,
            time_update=_iso_to_epoch(p.last_update),
            time_update_msc=_iso_to_epoch(p.last_update) * 1000,
            type=0 if str(p.side).upper() == "BUY" else 1,
            magic=p.magic,
            identifier=int(p.ticket),
            reason=0,
            volume=p.volume,
            price_open=p.entry_price if p.entry_price is not None else 0.0,
            sl=p.stop_loss,
            tp=p.take_profit,
            price_current=p.current_price if p.current_price is not None else 0.0,
            swap=p.swap,
            profit=p.profit if p.profit is not None else 0.0,
            symbol=p.symbol,
            comment=p.comment,
            external_id="",
        )

    def orders_get(self, symbol=None, group=None, ticket=None) -> list[_Struct] | None:
        try:
            account_id = self._resolve_account()
            pendings = self._ensure_client().orders.list_pending(account_id)
            out = []
            for o in pendings:
                if symbol is not None and o.symbol != symbol:
                    continue
                if group is not None and not fnmatch(o.symbol, group):
                    continue
                if ticket is not None and str(o.ticket) != str(ticket):
                    continue
                out.append(self._pending_struct(o))
            self._ok()
            return out
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll orders_get failed: %s", exc)
            return None

    @staticmethod
    def _pending_struct(o: Any) -> _Struct:
        setup = _iso_to_epoch(o.set_time)
        type_map = {
            ("limit", "BUY"): ORDER_TYPE_BUY_LIMIT,
            ("limit", "SELL"): ORDER_TYPE_SELL_LIMIT,
            ("stop", "BUY"): ORDER_TYPE_BUY_STOP,
            ("stop", "SELL"): ORDER_TYPE_SELL_STOP,
        }
        side = str(o.side).upper()
        otype = type_map.get((str(o.order_type).lower(), side), ORDER_TYPE_BUY_LIMIT)
        try:
            ticket_int = int(o.ticket)
        except (TypeError, ValueError):
            ticket_int = 0
        return _Struct(
            ticket=ticket_int,
            time_setup=setup,
            time_setup_msc=setup * 1000,
            time_expiration=_iso_to_epoch(o.expiration_time),
            type=otype,
            type_time=ORDER_TIME_GTC,
            type_filling=ORDER_FILLING_RETURN,
            state=1,
            magic=0,
            position_id=0,
            volume_initial=o.volume,
            volume_current=o.volume,
            price_open=o.price,
            sl=o.stop_loss,
            tp=o.take_profit,
            price_current=o.price,
            price_stoplimit=o.limit_price if o.limit_price is not None else 0.0,
            symbol=o.symbol,
            comment="",
            external_id="",
        )

    # -- history -----------------------------------------------------------
    def history_orders_get(self, **request: Any) -> list[_Struct] | None:
        try:
            account_id = self._resolve_account()
            kwargs = self._history_kwargs(request)
            orders = self._ensure_client().history.orders(account_id, **kwargs)
            position = request.get("position")
            out = []
            for o in orders:
                if position is not None and str(o.position_id) != str(position):
                    continue
                out.append(self._history_order_struct(o))
            self._ok()
            return out
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll history_orders_get failed: %s", exc)
            return None

    def history_deals_get(self, **request: Any) -> list[_Struct] | None:
        try:
            account_id = self._resolve_account()
            kwargs = self._history_kwargs(request)
            deals = self._ensure_client().history.deals(account_id, **kwargs)
            position = request.get("position")
            out = []
            for d in deals:
                if position is not None and str(d.position_id) != str(position):
                    continue
                out.append(self._history_deal_struct(d))
            self._ok()
            return out
        except Exception as exc:
            self._fail(RES_E_FAIL, str(exc))
            logger.error("TickerAll history_deals_get failed: %s", exc)
            return None

    @staticmethod
    def _history_kwargs(request: dict[str, Any]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if request.get("symbol") is not None:
            kwargs["symbol"] = request["symbol"]
        if request.get("from") is not None:
            kwargs["from_"] = request["from"]
        if request.get("to") is not None:
            kwargs["to"] = request["to"]
        return kwargs

    @staticmethod
    def _history_order_struct(o: Any) -> _Struct:
        setup = _iso_to_epoch(o.time)
        try:
            ticket_int = int(o.order_ticket)
        except (TypeError, ValueError):
            ticket_int = 0
        try:
            position_id = int(o.position_id)
        except (TypeError, ValueError):
            position_id = 0
        return _Struct(
            ticket=ticket_int,
            time_setup=setup,
            time_setup_msc=setup * 1000,
            time_expiration=0,
            type=0 if str(o.side).upper() == "BUY" else 1,
            type_time=ORDER_TIME_GTC,
            type_filling=ORDER_FILLING_RETURN,
            state=3,
            magic=0,
            position_id=position_id,
            position_by_id=0,
            reason=0,
            volume_initial=o.volume,
            volume_current=0.0,
            price_open=o.price,
            sl=0.0,
            tp=0.0,
            price_current=o.price,
            price_stoplimit=0.0,
            symbol=o.symbol,
            comment="",
            external_id="",
        )

    @staticmethod
    def _history_deal_struct(d: Any) -> _Struct:
        epoch = _iso_to_epoch(d.time)
        try:
            ticket_int = int(d.ticket)
        except (TypeError, ValueError):
            ticket_int = 0
        try:
            position_id = int(d.position_id)
        except (TypeError, ValueError):
            position_id = 0
        entry_map = {"in": 0, "out": 1, "inout": 2, "out_by": 3}
        return _Struct(
            ticket=ticket_int,
            order=0,
            time=epoch,
            time_msc=epoch * 1000,
            type=0 if str(d.side).upper() == "BUY" else 1,
            entry=entry_map.get(str(d.entry).lower(), 0),
            magic=0,
            position_id=position_id,
            reason=0,
            volume=d.volume,
            price=d.price,
            commission=0.0,
            swap=0.0,
            profit=0.0,
            fee=0.0,
            symbol=d.symbol,
            comment="",
            external_id="",
        )


# ---------------------------------------------------------------------------
# Module-level singleton + MetaTrader5-compatible function surface.
# ---------------------------------------------------------------------------
_provider: _Provider | None = None


def _p() -> _Provider:
    global _provider
    if _provider is None:
        _provider = _Provider()
    return _provider


def initialize(path: str | None = None, **kwargs: Any) -> bool:
    return _p().initialize(path)


def login(login: int, password: str = "", server: str = "", **kwargs: Any) -> bool:
    return _p().login(login, password, server)


def shutdown() -> bool:
    return _p().shutdown()


def list_accounts() -> list[dict[str, Any]]:
    return _p().list_accounts()


def use_account(account_id: str) -> dict[str, Any]:
    return _p().use_account(account_id)


def last_error() -> tuple[int, str]:
    return _p().last_error()


def account_info():
    return _p().account_info()


def terminal_info():
    return _p().terminal_info()


def version():
    return _p().version()


def symbols_get(group: str | None = None):
    return _p().symbols_get(group)


def symbol_info(symbol: str):
    return _p().symbol_info(symbol)


def symbol_info_tick(symbol: str):
    return _p().symbol_info_tick(symbol)


def symbol_select(symbol: str, visible: bool = True) -> bool:
    return _p().symbol_select(symbol, visible)


def copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int):
    return _p().copy_rates_from_pos(symbol, timeframe, start_pos, count)


def copy_rates_from_date(symbol: str, timeframe: int, date_from: datetime, count: int):
    return _p().copy_rates_from_date(symbol, timeframe, date_from, count)


def copy_rates_range(symbol: str, timeframe: int, date_from: datetime, date_to: datetime):
    return _p().copy_rates_range(symbol, timeframe, date_from, date_to)


def copy_ticks_from(symbol: str, date_from: datetime, count: int, flags: int = COPY_TICKS_ALL):
    return _p().copy_ticks_from(symbol, date_from, count, flags)


def copy_ticks_range(
    symbol: str, date_from: datetime, date_to: datetime, flags: int = COPY_TICKS_ALL
):
    return _p().copy_ticks_range(symbol, date_from, date_to, flags)


def order_send(request: dict[str, Any]):
    return _p().order_send(request)


def order_check(request: dict[str, Any]):
    return _p().order_check(request)


def positions_get(symbol=None, group=None, ticket=None):
    return _p().positions_get(symbol=symbol, group=group, ticket=ticket)


def orders_get(symbol=None, group=None, ticket=None):
    return _p().orders_get(symbol=symbol, group=group, ticket=ticket)


def history_orders_get(**request: Any):
    return _p().history_orders_get(**request)


def history_deals_get(**request: Any):
    return _p().history_deals_get(**request)
