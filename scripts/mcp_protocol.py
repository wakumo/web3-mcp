#!/usr/bin/env python3
"""Test MCP Protocol - Get latest block number of Ethereum"""

import asyncio
import json
import os
import sys


async def test_mcp_protocol():
    """Test calling MCP server via actual protocol"""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        print("❌ Need to install mcp SDK")
        print("   Run: uv add --dev mcp")
        return None

    print("=" * 70)
    print("TEST MCP PROTOCOL: Get Latest Block Number of Ethereum")
    print("=" * 70)

    # Get API key from environment variable
    private_key = os.environ.get("ANKR_PRIVATE_KEY") or os.environ.get("ANKR_API_KEY")

    if not private_key:
        print("\n❌ Need to set ANKR_PRIVATE_KEY environment variable")
        print("\n📝 Instructions:")
        print("   export ANKR_PRIVATE_KEY='your_api_key'")
        return None

    print("\n🚀 Starting MCP server...")

    # Configure server parameters to spawn MCP server
    # Get Python executable path
    python_exe = sys.executable

    server_params = StdioServerParameters(
        command=python_exe,
        args=["-m", "web3_mcp"],
        env={
            **os.environ,
            "ANKR_PRIVATE_KEY": private_key,
        },
    )

    try:
        print("🔌 Connecting to MCP server via STDIO...")

        # Connect to server and create session
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected successfully!")

                # Initialize session
                print("\n📋 Initializing session and getting list of tools...")
                await session.initialize()

                # List tools
                tools_list = await session.list_tools()

                print(f"   Server: Ankr MCP")
                print(f"   Number of tools: {len(tools_list.tools)}")

                # List some tools
                print("\n📦 Some available tools:")
                for i, tool in enumerate(tools_list.tools[:5]):
                    print(f"   - {tool.name}")
                if len(tools_list.tools) > 5:
                    print(f"   ... and {len(tools_list.tools) - 5} more tools")

                # Check if get_blockchain_stats tool exists
                tool_names = [tool.name for tool in tools_list.tools]
                if "get_blockchain_stats" not in tool_names:
                    print("\n❌ Tool 'get_blockchain_stats' is not available!")
                    return None

                print("\n🔍 Calling tool 'get_blockchain_stats' for Ethereum...")

                result = await session.call_tool(
                    "get_blockchain_stats", arguments={"request": {"blockchain": "eth"}}
                )

                print("✅ Received response from MCP server!")
                print(f"DEBUG - result: {result}")
                print(f"DEBUG - isError: {result.isError}")
                print(f"DEBUG - content: {result.content}")

                # Parse result
                if result and result.content:
                    for content in result.content:
                        if hasattr(content, "text"):
                            text = content.text
                            print(f"DEBUG - Raw text: {text}")

                            try:
                                data = json.loads(text)
                                print(f"DEBUG - Parsed data: {data}")
                            except json.JSONDecodeError as e:
                                print(f"DEBUG - JSON error: {e}")
                                continue

                            if isinstance(data, dict) and "stats" in data:
                                stats = data["stats"]
                                print(f"DEBUG - Stats: {stats}")

                                print("\n📊 Results:")
                                print(
                                    f"   Latest Block Number: {stats.get('lastBlockNumber', 'N/A')}"
                                )
                                print(
                                    f"   Total Transactions: {stats.get('transactions', 'N/A')}"
                                )
                                print(f"   TPS: {stats.get('tps', 'N/A')}")

                                block_number = stats.get("lastBlockNumber")

                                print("\n🔌 Disconnected from MCP server")
                                return block_number

                print("\n⚠️  Response format is not as expected")
                if result:
                    print(f"isError: {result.isError if hasattr(result, 'isError') else 'N/A'}")
                return None

    except Exception as e:
        print(f"\n❌ Error calling MCP: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


async def main():
    """Main function"""
    try:
        block_number = await test_mcp_protocol()
        if block_number:
            print(f"\n✨ Latest block number of Ethereum: {block_number}")
            print("\n✅ MCP protocol test successful!")
            sys.exit(0)
        else:
            print("\n❌ Test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
