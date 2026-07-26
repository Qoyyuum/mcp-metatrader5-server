"""MetaTrader 5 backend selector.

By default this server drives a local MetaTrader 5 terminal through the
official ``MetaTrader5`` Python package - which only runs on Windows with the
terminal installed. That is unchanged and remains the default.

Optionally, setting the ``TICKERALL_API_KEY`` environment variable switches the
backend to the **TickerAll hosted MT5 API** (https://tickerall.com), so the
exact same MCP tools run on Linux, macOS, or in a container with **no local MT5
terminal**. This is fully additive and opt-in:

* ``TICKERALL_API_KEY`` **unset**  -> the real ``MetaTrader5`` module is
  returned and behaviour is byte-for-byte identical to upstream.
* ``TICKERALL_API_KEY`` **set**    -> a drop-in, ``mt5``-shaped adapter backed
  by the hosted API is returned instead.

Nothing else in the codebase needs to know which one it got: both expose the
same ``initialize`` / ``login`` / ``symbol_info`` / ``order_send`` / ... surface
and the same ``TIMEFRAME_*`` / ``ORDER_*`` / ``TRADE_*`` constants.
"""

from __future__ import annotations

import os


def use_tickerall() -> bool:
    """True when the hosted TickerAll backend should be used."""
    return bool(os.getenv("TICKERALL_API_KEY"))


def get_backend():
    """Return the MT5 backend module/adapter to use (see module docstring)."""
    if use_tickerall():
        from mcp_mt5 import tickerall_backend

        return tickerall_backend

    import MetaTrader5 as mt5

    return mt5
