#!/usr/bin/env python3
"""Test tool get_nft_holders"""

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


async def test_get_nft_holders():
    """Test get_nft_holders tool"""
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
    print("TEST: get_nft_holders")
    print("=" * 70)

    # Test parameters
    blockchain = "eth"
    contract_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"  # Bored Ape Yacht Club
    page_size = 5

    print(f"\n📋 Parameters:")
    print(f"   Blockchain: {blockchain}")
    print(f"   Contract Address: {contract_address}")
    print(f"   Page Size: {page_size}")

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

                print(f"\n🔍 Calling tool 'get_nft_holders'...")
                result = await session.call_tool(
                    "get_nft_holders",
                    arguments={
                        "request": {
                            "blockchain": blockchain,
                            "contract_address": contract_address,
                            "page_size": page_size,
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
                            print(f"\n✅ Parsed JSON:")

                            # Display number of holders
                            if isinstance(data, dict):
                                if "holders" in data:
                                    holders = data["holders"]
                                    print(f"\n📦 Number of holders: {len(holders) if isinstance(holders, list) else 'N/A'}")

                                    # Display list of all holders
                                    if isinstance(holders, list) and len(holders) > 0:
                                        print(f"\n📋 List of all holders:")
                                        for i, holder in enumerate(holders):
                                            if isinstance(holder, dict):
                                                address = holder.get("holderAddress", holder.get("address", "N/A"))
                                                balance = holder.get("balance", holder.get("tokenBalance", "N/A"))
                                                print(f"   {i+1}. {address} - Balance: {balance}")

                                        # Display full JSON of all holders
                                        print(f"\n📄 Full JSON of all holders:")
                                        print(json.dumps(data, indent=2, ensure_ascii=False))

                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  Failed to parse JSON: {e}")

                print("\n✅ Test completed!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_get_nft_holders())
