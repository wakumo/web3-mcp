#!/usr/bin/env python3
"""Test tool get_nfts_by_owner"""

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


async def test_get_nfts_by_owner():
    """Test get_nfts_by_owner tool"""
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
    print("TEST: get_nfts_by_owner")
    print("=" * 70)

    # Test parameters
    wallet_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik's address
    blockchain = "eth"
    page_size = 5

    print(f"\n📋 Parameters:")
    print(f"   Wallet: {wallet_address}")
    print(f"   Blockchain: {blockchain}")
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

                print(f"\n🔍 Calling tool 'get_nfts_by_owner'...")
                result = await session.call_tool(
                    "get_nfts_by_owner",
                    arguments={
                        "request": {
                            "wallet_address": wallet_address,
                            "blockchain": blockchain,
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

                            # Display number of NFTs
                            if isinstance(data, dict):
                                if "assets" in data:
                                    assets = data["assets"]
                                    print(f"\n📦 Number of NFTs: {len(assets) if isinstance(assets, list) else 'N/A'}")

                                    # Display list of all NFTs
                                    if isinstance(assets, list) and len(assets) > 0:
                                        print(f"\n📋 List of all NFTs:")
                                        for i, asset in enumerate(assets):
                                            if isinstance(asset, dict):
                                                name = asset.get("name", asset.get("collectionName", "N/A"))
                                                symbol = asset.get("symbol", "N/A")
                                                token_id = asset.get("tokenId", "N/A")
                                                print(f"   {i+1}. {name} ({symbol}) - Token ID: {token_id}")

                                elif "nfts" in data:
                                    nfts = data["nfts"]
                                    print(f"\n📦 Number of NFTs: {len(nfts) if isinstance(nfts, list) else 'N/A'}")

                            # Display full JSON of all NFTs
                            print(f"\n📄 Full JSON of all NFTs:")
                            print(json.dumps(data, indent=2, ensure_ascii=False))

                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  Failed to parse JSON: {e}")

                print("\n✅ Test completed!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_get_nfts_by_owner())
