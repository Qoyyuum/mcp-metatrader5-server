"""Test client for MCP MetaTrader 5 Server

This demonstrates how to interact with the MCP server programmatically.
Make sure the server is running: uv run mt5mcp (with MT5_MCP_TRANSPORT=http in .env)
"""

import asyncio
import os

import dotenv
from fastmcp import Client

# Load environment variables from .env file
dotenv.load_dotenv()

# Configure the MCP server URL
MCP_SERVER_URL = "http://localhost:8000/mcp"

# MT5 Configuration - Update these with your details if auto-detection fails
MT5_PATH = os.getenv("MT5_PATH") or ""
MT5_LOGIN = int(os.getenv("MT5_LOGIN") or 123456)  # Your MT5 account number
MT5_PASSWORD = os.getenv("MT5_PASSWORD") or "your_password"  # Your MT5 password
MT5_SERVER = os.getenv("MT5_SERVER") or "YourBroker-Demo"  # Your broker server name


async def example_1_connection():
    """Example 1: Initialize and connect to MT5"""
    print("\n" + "=" * 60)
    print("Example 1: Initialize and Connect to MT5")
    print("=" * 60)

    async with Client(MCP_SERVER_URL) as client:
        # Initialize MT5
        print(f"Initializing MT5 at: {MT5_PATH or '<auto-detect>'}")
        result = await client.call_tool("initialize", {"path": MT5_PATH})

        # Check if initialization succeeded
        init_success = result.data if hasattr(result, "data") else False
        if not init_success:
            print("❌ MT5 initialization failed!")
            print("   Make sure:")
            print("   1. MetaTrader 5 terminal is running")
            print("   2. Path is correct")
            print("   3. MT5 terminal allows API access")
            return

        print("✓ Initialize result: Success")

        # Login to account
        print(f"\nLogging in to account: {MT5_LOGIN}")
        result = await client.call_tool(
            "login", {"login": MT5_LOGIN, "password": MT5_PASSWORD, "server": MT5_SERVER}
        )

        login_success = result.data if hasattr(result, "data") else False
        if not login_success:
            print("❌ MT5 login failed!")
            print("   Check your credentials in .env file")
            await client.call_tool("shutdown", {})
            return

        print("✓ Login result: Success")

        # Get account info
        print("\nGetting account information...")
        account_info = await client.call_tool("get_account_info", {})

        if hasattr(account_info, "data") and account_info.data:
            # Convert to dict if it's a Pydantic model or similar
            if hasattr(account_info.data, "model_dump"):
                info = account_info.data.model_dump()
            elif hasattr(account_info.data, "__dict__"):
                info = account_info.data.__dict__
            else:
                info = dict(account_info.data)

            print("✓ Account Info:")
            print(f"  - Balance: ${info.get('balance', 0):.2f}")
            print(f"  - Equity: ${info.get('equity', 0):.2f}")
            print(f"  - Leverage: 1:{info.get('leverage', 0)}")
        else:
            print("❌ Failed to get account info")

        # Shutdown
        print("\nShutting down MT5 connection...")
        await client.call_tool("shutdown", {})
        print("✓ Disconnected")


async def example_2_market_data():
    """Example 2: Get market data"""
    print("\n" + "=" * 60)
    print("Example 2: Get Market Data")
    print("=" * 60)

    async with Client(MCP_SERVER_URL) as client:
        # Initialize and login
        await client.call_tool("initialize", {"path": MT5_PATH})
        await client.call_tool(
            "login", {"login": MT5_LOGIN, "password": MT5_PASSWORD, "server": MT5_SERVER}
        )

        # Get available symbols
        print("\nGetting available symbols...")
        symbols_result = await client.call_tool("get_symbols", {})
        symbols = symbols_result.data if hasattr(symbols_result, "data") else []
        print(f"✓ Found {len(symbols)} symbols")
        print(f"  First 10: {symbols[:10]}")

        # Get symbol info for EURUSD
        symbol = "EURUSD"

        # Select symbol in Market Watch first (required for getting rates)
        print(f"\nSelecting {symbol} in Market Watch...")
        await client.call_tool("symbol_select", {"symbol": symbol, "visible": True})

        print(f"Getting info for {symbol}...")
        symbol_info_result = await client.call_tool("get_symbol_info", {"symbol": symbol})

        if hasattr(symbol_info_result, "data") and symbol_info_result.data:
            if hasattr(symbol_info_result.data, "model_dump"):
                symbol_info = symbol_info_result.data.model_dump()
            elif hasattr(symbol_info_result.data, "__dict__"):
                symbol_info = symbol_info_result.data.__dict__
            else:
                symbol_info = dict(symbol_info_result.data)

            print(f"✓ {symbol} Info:")
            print(f"  - Bid: {symbol_info.get('bid', 0)}")
            print(f"  - Ask: {symbol_info.get('ask', 0)}")
            print(f"  - Spread: {symbol_info.get('spread', 0)} points")

        # Get latest tick
        print(f"\nGetting latest tick for {symbol}...")
        tick_result = await client.call_tool("get_symbol_info_tick", {"symbol": symbol})

        if hasattr(tick_result, "data") and tick_result.data:
            tick = (
                tick_result.data if isinstance(tick_result.data, dict) else dict(tick_result.data)
            )
            print("✓ Latest Tick:")
            print(f"  - Bid: {tick.get('bid', 0)}")
            print(f"  - Ask: {tick.get('ask', 0)}")
            print(f"  - Volume: {tick.get('volume', 0)}")

        # Get price bars
        print(f"\nGetting last 5 bars for {symbol} on H1...")
        rates_result = await client.call_tool(
            "copy_rates_from_pos",
            {
                "symbol": symbol,
                "timeframe": 60,  # H1
                "start_pos": 0,
                "count": 5,
            },
        )

        if hasattr(rates_result, "data") and rates_result.data:
            rates = rates_result.data
            print(f"✓ Retrieved {len(rates)} bars")
            for i, bar in enumerate(rates[:3], 1):
                # Convert bar object to dict
                if isinstance(bar, dict):
                    bar_dict = bar
                elif hasattr(bar, "model_dump"):
                    bar_dict = bar.model_dump()
                elif hasattr(bar, "__dict__"):
                    bar_dict = bar.__dict__
                else:
                    # Try to access attributes directly
                    bar_dict = {
                        "open": getattr(bar, "open", None),
                        "high": getattr(bar, "high", None),
                        "low": getattr(bar, "low", None),
                        "close": getattr(bar, "close", None),
                    }
                print(
                    f"  Bar {i}: O={bar_dict.get('open')} H={bar_dict.get('high')} L={bar_dict.get('low')} C={bar_dict.get('close')}"
                )

        # Shutdown
        await client.call_tool("shutdown", {})


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("MCP MetaTrader 5 Server - Test Client")
    print("=" * 60)
    print("\n⚠️  Before running:")
    print("1. Update MT5_LOGIN, MT5_PASSWORD, MT5_SERVER in this file")
    print("   Set MT5_PATH only if auto-detection fails")
    print("2. Start the MCP server with HTTP mode: uv run mt5mcp")
    print("3. Make sure MT5 terminal is running")

    try:
        await example_1_connection()
        await example_2_market_data()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
