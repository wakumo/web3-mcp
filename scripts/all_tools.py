#!/usr/bin/env python3
"""Test all MCP tools systematically"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

# Load .env file if exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, skip


async def test_tool(session, tool_name: str, arguments: Dict[str, Any], description: str) -> bool:
    """Test a tool and return True if successful"""
    print(f"\n{'='*70}")
    print(f"🔍 TEST: {tool_name}")
    print(f"📝 Description: {description}")
    print(f"📋 Arguments: {json.dumps(arguments, indent=2)}")
    print(f"{'='*70}")

    try:
        result = await session.call_tool(tool_name, arguments=arguments)

        if result.isError:
            print(f"❌ Tool returned error: {result.content}")
            return False

        if not result.content:
            print(f"⚠️  Tool did not return content")
            return False

        # Parse and display results
        success = False
        for content in result.content:
            if hasattr(content, "text"):
                text = content.text
                try:
                    data = json.loads(text)
                    print(f"✅ Response (JSON):")
                    print(json.dumps(data, indent=2)[:500])  # Limit output
                    if len(json.dumps(data, indent=2)) > 500:
                        print("... (truncated)")
                    success = True
                except json.JSONDecodeError:
                    print(f"✅ Response (text): {text[:200]}")
                    success = True

        if success:
            print(f"✅ Tool '{tool_name}' works correctly!")
            return True
        else:
            print(f"⚠️  Failed to parse response")
            return False

    except Exception as e:
        print(f"❌ Error calling tool: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_all_tools():
    """Test all tools"""
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
    print("TEST ALL MCP TOOLS")
    print("=" * 70)

    python_exe = sys.executable
    server_params = StdioServerParameters(
        command=python_exe,
        args=["-m", "web3_mcp"],
        env={
            **os.environ,
            "ANKR_PRIVATE_KEY": private_key,
        },
    )

    # Test data - using reasonable values
    ETH_BLOCKCHAIN = "eth"
    TEST_WALLET = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik's address
    TEST_CONTRACT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC on Ethereum
    TEST_NFT_CONTRACT = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"  # Bored Ape Yacht Club
    TEST_TOKEN_ID = "1"
    TEST_TX_HASH = "0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060"  # Example tx

    results = {}

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Test 1: get_blockchain_stats
                results["get_blockchain_stats"] = await test_tool(
                    session,
                    "get_blockchain_stats",
                    {"request": {"blockchain": ETH_BLOCKCHAIN}},
                    "Get Ethereum blockchain statistics"
                )

                # Test 2: get_supported_networks (no arguments needed)
                results["get_supported_networks"] = await test_tool(
                    session,
                    "get_supported_networks",
                    {},
                    "Get list of supported networks"
                )

                # Test 3: get_currencies
                results["get_currencies"] = await test_tool(
                    session,
                    "get_currencies",
                    {"request": {"blockchain": ETH_BLOCKCHAIN}},
                    "Get list of currencies on Ethereum"
                )

                # Test 4: get_account_balance
                results["get_account_balance"] = await test_tool(
                    session,
                    "get_account_balance",
                    {"request": {"wallet_address": TEST_WALLET, "blockchain": ETH_BLOCKCHAIN}},
                    f"Get balance of wallet {TEST_WALLET}"
                )

                # Test 5: get_token_price
                results["get_token_price"] = await test_tool(
                    session,
                    "get_token_price",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "contract_address": TEST_CONTRACT}},
                    f"Get price of token {TEST_CONTRACT} (USDC)"
                )

                # Test 6: get_token_holders_count
                results["get_token_holders_count"] = await test_tool(
                    session,
                    "get_token_holders_count",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "contract_address": TEST_CONTRACT}},
                    f"Get number of holders of token {TEST_CONTRACT}"
                )

                # Test 7: get_blocks
                results["get_blocks"] = await test_tool(
                    session,
                    "get_blocks",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "page_size": 5}},
                    "Get 5 latest blocks of Ethereum"
                )

                # Test 8: get_nfts_by_owner
                results["get_nfts_by_owner"] = await test_tool(
                    session,
                    "get_nfts_by_owner",
                    {"request": {"wallet_address": TEST_WALLET, "blockchain": ETH_BLOCKCHAIN, "page_size": 5}},
                    f"Get NFTs of wallet {TEST_WALLET}"
                )

                # Test 9: get_nft_metadata
                results["get_nft_metadata"] = await test_tool(
                    session,
                    "get_nft_metadata",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "contract_address": TEST_NFT_CONTRACT, "token_id": TEST_TOKEN_ID}},
                    f"Get metadata of NFT {TEST_NFT_CONTRACT} token {TEST_TOKEN_ID}"
                )

                # Test 10: get_nft_holders
                results["get_nft_holders"] = await test_tool(
                    session,
                    "get_nft_holders",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "contract_address": TEST_NFT_CONTRACT, "page_size": 5}},
                    f"Get holders of NFT collection {TEST_NFT_CONTRACT}"
                )

                # Test 11: get_nft_transfers
                results["get_nft_transfers"] = await test_tool(
                    session,
                    "get_nft_transfers",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "contract_address": TEST_NFT_CONTRACT, "page_size": 5}},
                    f"Get transfers of NFT collection {TEST_NFT_CONTRACT}"
                )

                # Test 12: get_transactions_by_address
                results["get_transactions_by_address"] = await test_tool(
                    session,
                    "get_transactions_by_address",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "wallet_address": TEST_WALLET, "page_size": 5}},
                    f"Get transactions of wallet {TEST_WALLET}"
                )

                # Test 13: get_token_holders
                results["get_token_holders"] = await test_tool(
                    session,
                    "get_token_holders",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "contract_address": TEST_CONTRACT, "page_size": 5}},
                    f"Get holders of token {TEST_CONTRACT}"
                )

                # Test 14: get_token_transfers
                results["get_token_transfers"] = await test_tool(
                    session,
                    "get_token_transfers",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "contract_address": TEST_CONTRACT, "page_size": 5}},
                    f"Get transfers of token {TEST_CONTRACT}"
                )

                # Test 15: get_interactions
                results["get_interactions"] = await test_tool(
                    session,
                    "get_interactions",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "wallet_address": TEST_WALLET, "page_size": 5}},
                    f"Get interactions of wallet {TEST_WALLET}"
                )

                # Test 16: get_logs (requires contract address)
                results["get_logs"] = await test_tool(
                    session,
                    "get_logs",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "address": TEST_CONTRACT, "page_size": 5}},
                    f"Get logs of contract {TEST_CONTRACT}"
                )

                # Test 17: get_transactions_by_hash
                results["get_transactions_by_hash"] = await test_tool(
                    session,
                    "get_transactions_by_hash",
                    {"request": {"blockchain": ETH_BLOCKCHAIN, "transaction_hash": TEST_TX_HASH}},
                    f"Get transaction details of hash {TEST_TX_HASH}"
                )

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)

    total = len([r for r in results.values() if r is not None])
    passed = len([r for r in results.values() if r is True])
    failed = len([r for r in results.values() if r is False])
    skipped = len([r for r in results.values() if r is None])

    for tool_name, result in results.items():
        if result is True:
            print(f"✅ {tool_name}")
        elif result is False:
            print(f"❌ {tool_name}")
        else:
            print(f"⏭️  {tool_name} (skipped)")

    print(f"\n📈 Statistics:")
    print(f"   Total tools: {total + skipped}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   📊 Success rate: {passed}/{total} ({passed*100//total if total > 0 else 0}%)")


if __name__ == "__main__":
    asyncio.run(test_all_tools())
