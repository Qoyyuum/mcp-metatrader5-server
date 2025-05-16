"""
Test script for interacting with MT5 MCP Server using LangChain and LangGraph.

This script creates a simple agent that can query the MT5 MCP server
to check for open positions and other trading data. Uses Claude as the LLM.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def run_agent_with_mt5_tools():
    """
    Create and run a LangGraph agent that can interact with MT5 MCP server.
    Uses the agent to check for open positions via the MCP server.
    """
    # Initial prompt to check open trading positions
    initial_prompt = """
First, initialize a connection to the MT5 terminal by calling the initialize() tool.
Then, log in to my trading account using these credentials:

- Account: 42032765
- Password: !s@n^I9n 
- Server: FBS-Real

After successfully logging in, check if there are any open positions in my MT5 trading account and list them if they exist.
"""
    
    # Set up the MCP client for the MT5 server
    client = MultiServerMCPClient(
        {
            "mt5": {
                "transport": "sse",
                "url": "http://localhost:8000/sse"
            },
        }
    )
    
    # Initialize Claude model (similar to high_impact_news.py)
    model = ChatAnthropic(
        model_name="claude-3-5-sonnet-20240620",
        temperature=0.0,
        timeout=100,
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )
    
    logger.info("Connecting to MT5 MCP server and loading tools...")
    
    # Get tools from the MCP server
    tools = await client.get_tools()
    
    logger.info(f"Successfully loaded {len(tools)} tools from MT5 MCP server")
    
    # Create the agent with Claude and the MT5 tools
    agent = create_react_agent(model, tools)
    
    logger.info("Running agent with prompt: " + initial_prompt)
    
    # Run the agent with the initial prompt
    response = await agent.ainvoke({"messages": initial_prompt})
    
    # Print the agent's response
    print("\n=== Agent Response ===")
    print(response["messages"][-1].content)
    print("=====================\n")
    
    return response

async def main():
    """Main function to run the MT5 MCP test."""
    print("Starting MT5 MCP server test...")
    logger.info("Make sure the MT5 MCP server is running: mt5-mcp dev")
    
    try:
        await run_agent_with_mt5_tools()
        print("Test completed successfully.")
    except Exception as e:
        logger.error(f"Error during test: {e}")
        print(f"An error occurred: {e}")
        print("Make sure MetaTrader 5 terminal is running and the MCP server is started.")

if __name__ == "__main__":
    asyncio.run(main())
