#!/usr/bin/env python3
"""Test tool get_token_price"""

import asyncio
import json
import os
import sys

# Load .env file if exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


async def test_get_token_price():
    """Test get_token_price tool"""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        print("❌ Need to install mcp SDK")
        print("   Run: uv add --dev mcp")
        return

    private_key = os.environ.get("ANKR_PRIVATE_KEY") or os.environ.get("ANKR_API_KEY")
    if not private_key:
        print("❌ Need to set ANKR_PRIVATE_KEY environment variable")
        return

    print("=" * 70)
    print("TEST: get_token_price")
    print("=" * 70)

    # Test parameters
    blockchain = "eth"  # chain_id 1 = Ethereum
    # contract_address = "0xdDFbE9173c90dEb428fdD494cB16125653172919"  # Token with price 0
    contract_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC (should have price ~$1)

    print(f"\n📋 Parameters:")
    print(f"   Blockchain: {blockchain} (chain_id: 1)")
    print(f"   Contract Address: {contract_address}")

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
        print("\n🔌 Connecting to MCP server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ Connected successfully!")

                print(f"\n🔍 Calling tool 'get_token_price'...")
                result = await session.call_tool(
                    "get_token_price",
                    arguments={
                        "request": {
                            "blockchain": blockchain,
                            "contract_address": contract_address,
                        }
                    },
                )

                print(f"\n📊 Response:")
                print(f"   isError: {result.isError}")

                if result.isError:
                    print(f"❌ Tool returned error:")
                    for content in result.content:
                        if hasattr(content, "text"):
                            print(f"   {content.text}")
                    return

                if not result.content:
                    print("⚠️  Tool did not return content")
                    return

                # Parse and display results
                for content in result.content:
                    if hasattr(content, "text"):
                        text = content.text
                        print(f"\n📄 Raw response:")
                        print(text[:500])
                        if len(text) > 500:
                            print("... (truncated)")

                        try:
                            data = json.loads(text)
                            print(f"\n✅ Full JSON response:")
                            print(json.dumps(data, indent=2, ensure_ascii=False))

                            # Display price if available
                            if isinstance(data, dict):
                                if "price_usd" in data:
                                    print(f"\n💰 Token Price: ${data['price_usd']} USD")
                                elif "prices" in data:
                                    prices = data["prices"]
                                    if isinstance(prices, list) and len(prices) > 0:
                                        print(f"\n💰 Token Prices:")
                                        for price in prices:
                                            print(f"   {json.dumps(price, indent=2)}")

                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  Failed to parse JSON: {e}")
                            print(f"Raw text: {text}")

                print("\n✅ Test completed!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_get_token_price())
