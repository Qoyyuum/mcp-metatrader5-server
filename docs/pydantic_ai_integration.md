# Pydantic AI Integration Guide

This guide demonstrates how to integrate the MetaTrader 5 MCP Server with [Pydantic AI](https://ai.pydantic.dev/), a Python framework for building production-grade AI agents with type safety and structured outputs.

## What is Pydantic AI?

Pydantic AI is a Python agent framework designed to make it easy to build production-grade applications with Generative AI. It provides:

- **Type-safe agent development** using Pydantic models
- **Model-agnostic design** supporting OpenAI, Anthropic, Gemini, and more
- **Structured outputs** with validation
- **Tool/function calling** with type hints
- **Dependency injection** for clean architecture

## Prerequisites

- Python 3.11 or higher
- MetaTrader 5 terminal installed on Windows
- MCP MetaTrader 5 Server installed
- Pydantic AI installed

## Installation

```bash
# Install Pydantic AI
pip install pydantic-ai

# Or with specific model support
pip install 'pydantic-ai[openai]'  # For OpenAI
pip install 'pydantic-ai[anthropic]'  # For Anthropic Claude
pip install 'pydantic-ai[gemini]'  # For Google Gemini

# Install the MCP MetaTrader 5 Server
pip install mcp-metatrader5-server

# Or install from source
git clone https://github.com/Qoyyuum/mcp-metatrader5-server
cd mcp-metatrader5-server
uv sync
```

## Architecture Overview

The integration combines three components:

1. **Pydantic AI Agent** - Orchestrates the AI logic and tool calls
2. **MCP Client** - Communicates with the MCP server using the Model Context Protocol
3. **MT5 MCP Server** - Provides tools to interact with MetaTrader 5

```text
┌─────────────────────┐
│   Pydantic AI       │
│     Agent           │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   MCP Client        │
│   (via stdio/http)  │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│ MT5 MCP Server      │
│  (FastMCP)          │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  MetaTrader 5       │
│    Terminal         │
└─────────────────────┘
```

## Basic Integration Example

Here's a minimal example of using the MT5 MCP Server with Pydantic AI:

```python
import asyncio
from datetime import datetime
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Initialize the Pydantic AI agent
model = OpenAIModel('gpt-4o', api_key='your-api-key-here')
agent = Agent(
    model,
    system_prompt="""You are a trading assistant with access to MetaTrader 5.
    You can help analyze markets, retrieve data, and execute trades safely."""
)

async def use_mt5_with_pydantic_ai():
    # Start the MCP server connection
    server_params = StdioServerParameters(
        command="uvx",
        args=["--from", "mcp-metatrader5-server", "mt5mcp"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools from the MCP server
            tools_result = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools_result.tools]}")
            
            # Call a tool - Initialize MT5
            init_result = await session.call_tool(
                "initialize",
                arguments={"path": ""}
            )
            print(f"MT5 Initialization: {init_result.content}")
            
            # Get account info using the agent
            result = await agent.run(
                "Get my account information and summarize the balance and equity.",
                message_history=[]
            )
            print(f"Agent response: {result.data}")

# Run the async function
asyncio.run(use_mt5_with_pydantic_ai())
```

## Advanced Example: Trading Assistant Agent

This example shows a more sophisticated agent that can analyze market data and execute trades:

```python
import asyncio
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.mcp import MCPServerStdio
import os
import dotenv

dotenv.load_dotenv()
# Define structured output for market analysis
class MarketAnalysis(BaseModel):
    """Market analysis result"""
    symbol: str
    timeframe: int
    trend: str = Field(description="Current market trend: bullish, bearish, or sideways")
    support_level: float | None = Field(default=None, description="Key support level")
    resistance_level: float | None = Field(default=None, description="Key resistance level")
    recommendation: str = Field(description="Trading recommendation")
    risk_level: str = Field(description="Risk level: low, medium, or high")

# Setup MCP server for MetaTrader 5
mt5_server = MCPServerStdio(
    'uvx',
    args=['--from', 'mcp-metatrader5-server', 'mt5mcp'],
    timeout=30
)

# Create the AI model
model = OpenAIChatModel(
    'mistralai/mistral-small-3.2-24b-instruct:free',
    provider=OpenRouterProvider(api_key=os.getenv("OPENROUTER_API_KEY"))
)

# Create the trading agent with MT5 MCP server as a toolset
trading_agent = Agent(
    model,
    output_type=MarketAnalysis,
    system_prompt="""You are an expert trading analyst with access to MetaTrader 5 market data.
    
    Your responsibilities:
    1. Initialize MetaTrader 5 first using the initialize tool
    2. Analyze market data using technical indicators
    3. Identify key support and resistance levels
    4. Determine market trends (bullish, bearish, sideways)
    5. Provide clear trading recommendations
    6. Assess risk levels for each recommendation
    
    Always consider:
    - Multiple timeframe analysis
    - Risk management principles
    - Market volatility
    - Recent price action
    
    Available tools from MT5:
    - initialize: Initialize MT5 connection
    - copy_rates_from_pos: Get historical price data
    - get_symbol_info_tick: Get current price tick
    - get_account_info: Get account balance and info
    - positions_get: Get open positions
    - shutdown: Shutdown MT5 connection
    
    Be conservative with recommendations and always prioritize capital preservation.""",
    toolsets=[mt5_server],  # Register MT5 MCP server as a toolset
    retries=2
)

# Run the trading agent
async def run_trading_analysis():
    """Run a complete market analysis using the trading agent with MCP"""
    
    # Use the agent context manager which handles MCP server lifecycle
    async with trading_agent:
        print("\n🔍 Analyzing EURUSD market...")
        
        # The agent will automatically use the MT5 MCP tools
        result = await trading_agent.run(
            """Analyze the EURUSD market on the 1-hour timeframe.
            
            Steps to follow:
            1. First initialize MetaTrader 5 with path: C:\\Program Files\\MetaTrader 5\\terminal64.exe
            2. Get the last 100 bars of price data for EURUSD on 60-minute timeframe
            3. Get the current price for EURUSD
            4. Analyze the data to identify the trend
            5. Find key support and resistance levels
            6. Provide a trading recommendation with risk assessment
            7. Finally, shutdown the MT5 connection
            
            Return your analysis in the structured format.
            """
        )
        
        # Display results
        print("\n📊 Market Analysis Results:")
        print(f"Symbol: {result.output.symbol}")
        print(f"Timeframe: {result.output.timeframe} minutes")
        print(f"Trend: {result.output.trend}")
        print(f"Support: {result.output.support_level}")
        print(f"Resistance: {result.output.resistance_level}")
        print(f"Recommendation: {result.output.recommendation}")
        print(f"Risk Level: {result.output.risk_level}")

# Run the analysis
if __name__ == "__main__":
    asyncio.run(run_trading_analysis())
```

## Example: Automated Trading Bot

Here's a complete example of an automated trading bot using Pydantic AI and the MT5 MCP Server:

```python
import asyncio
from datetime import datetime
from typing import Any, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class TradingDecision(BaseModel):
    """Structured trading decision"""
    should_trade: bool
    action: str | None = Field(default=None, description="BUY or SELL")
    symbol: str
    volume: float = 0.1
    stop_loss: float | None = None
    take_profit: float | None = None
    reason: str = Field(description="Reason for the decision")

class TradingBot:
    """Automated trading bot using Pydantic AI and MT5 MCP"""
    
    def __init__(self, api_key: str, mt5_path: str):
        self.mt5_path = mt5_path
        
        # Create the decision-making agent
        model = AnthropicModel('claude-3-5-sonnet-20241022', api_key=api_key)
        self.agent = Agent(
            model,
            result_type=TradingDecision,
            system_prompt="""You are a conservative trading bot focused on capital preservation.
            
            Rules:
            1. Only trade when you have high confidence (>80%)
            2. Always use stop loss and take profit
            3. Maximum risk per trade: 2% of account balance
            4. Prefer trending markets over ranging markets
            5. Never trade during high-impact news events
            6. Always check existing positions before opening new ones
            
            Decision criteria:
            - Strong trend confirmation
            - Clear support/resistance levels
            - Risk/reward ratio of at least 1:2
            - Favorable market conditions""",
        )
        
        # Add tools
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools with the agent"""
        
        @self.agent.tool
        async def analyze_trend(
            ctx: RunContext[Any],
            symbol: str,
            timeframe: int = 240  # 4-hour
        ) -> str:
            """Analyze market trend for a symbol"""
            # Get 200 bars for trend analysis
            result = await ctx.deps.session.call_tool(
                "copy_rates_from_pos",
                arguments={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "start_pos": 0,
                    "count": 200
                }
            )
            # Return the data for AI to analyze
            return f"Price data retrieved: {len(result.content)} bars"
        
        @self.agent.tool
        async def check_positions(
            ctx: RunContext[Any],
            symbol: str | None = None
        ) -> int:
            """Check number of open positions"""
            args = {"symbol": symbol} if symbol else {}
            result = await ctx.deps.session.call_tool(
                "positions_get",
                arguments=args
            )
            positions = result.content[0].text if result.content else []
            return len(positions) if isinstance(positions, list) else 0
        
        @self.agent.tool
        async def get_balance(ctx: RunContext[Any]) -> float:
            """Get account balance"""
            result = await ctx.deps.session.call_tool(
                "get_account_info",
                arguments={}
            )
            # Parse and return balance
            return 10000.0  # Placeholder
    
    async def make_trading_decision(
        self,
        session: ClientSession,
        symbol: str,
        timeframe: int = 240
    ) -> TradingDecision:
        """Make a trading decision for a symbol"""
        
        class Deps(BaseModel):
            session: Any = Field(exclude=True)
        
        deps = Deps(session=session)
        
        result = await self.agent.run(
            f"""Analyze {symbol} on the {timeframe}-minute timeframe and decide if we should trade.
            
            Consider:
            1. Current trend direction
            2. Existing positions (don't over-trade)
            3. Account balance and risk
            4. Support/resistance levels
            5. Overall market conditions
            
            Provide your decision with clear reasoning.""",
            deps=deps
        )
        
        return result.data
    
    async def execute_trade(
        self,
        session: ClientSession,
        decision: TradingDecision
    ) -> dict:
        """Execute a trade based on the decision"""
        
        if not decision.should_trade:
            return {"status": "skipped", "reason": decision.reason}
        
        # Get current price
        tick_result = await session.call_tool(
            "get_symbol_info_tick",
            arguments={"symbol": decision.symbol}
        )
        
        # Prepare order (simplified - should include proper price, SL, TP calculation)
        order_params = {
            "action": 1,  # TRADE_ACTION_DEAL
            "symbol": decision.symbol,
            "volume": decision.volume,
            "type": 0 if decision.action == "BUY" else 1,
            "price": 1.1000,  # Should use actual price from tick_result
            "sl": decision.stop_loss or 0.0,
            "tp": decision.take_profit or 0.0,
            "deviation": 20,
            "magic": 123456,
            "comment": f"PydanticAI: {decision.reason[:50]}",
            "type_filling": 2  # IOC
        }
        
        # Send order
        result = await session.call_tool(
            "order_send",
            arguments={"request": order_params}
        )
        
        return {"status": "executed", "result": result.content}
    
    async def run(self, symbols: List[str], login: int, password: str, server: str):
        """Run the trading bot"""
        
        server_params = StdioServerParameters(
            command="uvx",
            args=["--from", "mcp-metatrader5-server", "mt5mcp"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                await session.call_tool(
                    "initialize",
                    arguments={"path": self.mt5_path}
                )
                await session.call_tool(
                    "login",
                    arguments={
                        "login": login,
                        "password": password,
                        "server": server
                    }
                )
                
                print("🤖 Trading bot started")
                
                # Analyze each symbol
                for symbol in symbols:
                    print(f"\n📊 Analyzing {symbol}...")
                    decision = await self.make_trading_decision(session, symbol)
                    
                    print(f"Decision: {'TRADE' if decision.should_trade else 'SKIP'}")
                    print(f"Reason: {decision.reason}")
                    
                    if decision.should_trade:
                        result = await self.execute_trade(session, decision)
                        print(f"Trade result: {result['status']}")
                
                # Cleanup
                await session.call_tool("shutdown", arguments={})
                print("\n✅ Trading bot completed")

# Usage
async def main():
    bot = TradingBot(
        api_key="your-anthropic-api-key",
        mt5_path=""
    )
    
    await bot.run(
        symbols=["EURUSD", "GBPUSD", "USDJPY"],
        login=123456,
        password="your-password",
        server="your-server"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices

### 1. Error Handling

Always handle MCP call failures gracefully:

```python
try:
    result = await session.call_tool("get_account_info", arguments={})
    if result.isError:
        print(f"Error: {result.content}")
    else:
        account_info = result.content[0].text
except Exception as e:
    print(f"MCP call failed: {e}")
```

### 2. Connection Management

Properly manage the MCP session lifecycle:

```python
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize at start
        await session.initialize()
        
        try:
            # Your trading logic here
            pass
        finally:
            # Always shutdown MT5
            await session.call_tool("shutdown", arguments={})
```

### 3. Type Safety

Use Pydantic models for structured outputs:

```python
class AccountSummary(BaseModel):
    balance: float
    equity: float
    margin_free: float
    margin_level: float
    
agent = Agent(model, result_type=AccountSummary)
result = await agent.run("Get my account summary", deps=deps)
# result.data is typed as AccountSummary
```

### 4. Dependency Injection

Inject the MCP session and configuration:

```python
class TradingDeps(BaseModel):
    session: Any = Field(exclude=True)
    max_risk_per_trade: float = 0.02
    max_open_positions: int = 3

agent = Agent(model, deps_type=TradingDeps)
```

### 5. Retry Logic

Use Pydantic AI's built-in retry mechanism:

```python
agent = Agent(
    model,
    retries=3,  # Retry failed calls up to 3 times
    result_retries=2  # Retry result validation failures
)
```

## Common Patterns

### Pattern 1: Multi-Timeframe Analysis

```python
async def analyze_multiple_timeframes(session, symbol: str):
    """Analyze a symbol across multiple timeframes"""
    timeframes = [15, 60, 240, 1440]  # 15min, 1h, 4h, 1day
    
    analyses = {}
    for tf in timeframes:
        result = await session.call_tool(
            "copy_rates_from_pos",
            arguments={"symbol": symbol, "timeframe": tf, "start_pos": 0, "count": 100}
        )
        analyses[f"{tf}min"] = result.content
    
    return analyses
```

### Pattern 2: Risk Management

```python
async def calculate_position_size(
    session,
    symbol: str,
    balance: float,
    risk_percent: float = 0.02,
    stop_loss_pips: int = 50
) -> float:
    """Calculate position size based on risk"""
    symbol_info = await session.call_tool(
        "get_symbol_info",
        arguments={"symbol": symbol}
    )
    
    # Calculate position size
    risk_amount = balance * risk_percent
    pip_value = 10  # Simplified, should calculate from symbol_info
    position_size = risk_amount / (stop_loss_pips * pip_value)
    
    return round(position_size, 2)
```

### Pattern 3: Monitoring Loop

```python
async def monitor_positions(session, interval_seconds: int = 60):
    """Continuously monitor open positions"""
    while True:
        positions = await session.call_tool(
            "positions_get",
            arguments={}
        )
        
        for position in positions.content[0].text:
            # Check if stop loss or take profit should be adjusted
            # Check for trailing stop logic
            # Log position status
            pass
        
        await asyncio.sleep(interval_seconds)
```

## Troubleshooting

### Issue: MCP Server Not Starting

**Solution**: Verify the server path and check it's installed:

```bash
uvx --from mcp-metatrader5-server mt5mcp --help
```

### Issue: MT5 Connection Failed

**Solution**: Try the default auto-detected terminal first. If that fails, ensure
MT5 terminal is installed and pass the full path to `terminal64.exe`:

```python
# Try auto-detection first, then fallback paths
paths = [
    "",
    r"C:\Program Files\MetaTrader 5\terminal64.exe",
    r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
]

for path in paths:
    result = await session.call_tool("initialize", arguments={"path": path})
    if not result.isError:
        break
```

### Issue: Tool Calls Failing

**Solution**: Check tool availability and parameters:

```python
# List all available tools
tools = await session.list_tools()
for tool in tools.tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Parameters: {tool.inputSchema}")
```

## Resources

- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [MetaTrader 5 Python Documentation](https://www.mql5.com/en/docs/python_metatrader5)
- [MCP MetaTrader 5 Server Repository](https://github.com/Qoyyuum/mcp-metatrader5-server)

## Next Steps

1. Review the [API Reference](api_reference.md) for available tools
2. Check the [Trading Guide](trading_guide.md) for trade execution details
3. Explore the [Market Data Guide](market_data_guide.md) for data analysis
4. Build your custom trading agents with Pydantic AI's advanced features

## License

This integration guide is part of the MCP MetaTrader 5 Server project and is licensed under the MIT License.
