#!/usr/bin/env python3
"""Test tool get_transactions_by_hash"""

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


async def test_get_transactions_by_hash():
    """Test get_transactions_by_hash tool"""
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
    print("TEST: get_transactions_by_hash")
    print("=" * 70)

    # Test parameters
    # Using a well-known Ethereum transaction hash
    transaction_hash = "0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060"
    blockchain = "eth"

    print(f"\n📋 Parameters:")
    print(f"   Transaction Hash: {transaction_hash}")
    print(f"   Blockchain: {blockchain}")

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

                print(f"\n🔍 Calling tool 'get_transactions_by_hash'...")
                result = await session.call_tool(
                    "get_transactions_by_hash",
                    arguments={
                        "request": {
                            "transaction_hash": transaction_hash,
                            "blockchain": blockchain,
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

                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  Failed to parse JSON: {e}")
                            print(f"Raw text: {text}")

                print("\n✅ Test completed!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_get_transactions_by_hash())
