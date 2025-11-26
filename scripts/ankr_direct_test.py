#!/usr/bin/env python3
"""Test Ankr API directly to create curl command"""

import os
import json
from ankr import AnkrWeb3
from ankr.types import GetNFTsByOwnerRequest

# Load API key
api_key = os.environ.get("ANKR_PRIVATE_KEY") or os.environ.get("ANKR_API_KEY")
if not api_key:
    print("❌ Need to set ANKR_PRIVATE_KEY")
    exit(1)

print("=" * 70)
print("TEST ANKR API DIRECTLY")
print("=" * 70)

# Initialize client
client = AnkrWeb3(api_key=api_key)

# Test data
wallet_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik
blockchain = "eth"
page_size = 5

print(f"\n📋 Test Parameters:")
print(f"   Wallet: {wallet_address}")
print(f"   Blockchain: {blockchain}")
print(f"   Page Size: {page_size}")

# Create request
request = GetNFTsByOwnerRequest(
    walletAddress=wallet_address,
    blockchain=blockchain,
    pageSize=page_size
)

print(f"\n🔍 Calling Ankr API...")
try:
    result = client.nft.get_nfts(request)
    print(f"✅ API call successful!")
    print(f"📊 Result type: {type(result)}")

    if result:
        assets = list(result) if hasattr(result, "__iter__") else [result]
        print(f"📦 Number of NFTs: {len(assets)}")

        if assets:
            print(f"\n📄 First NFT:")
            first_nft = assets[0]
            if hasattr(first_nft, "__dict__"):
                print(json.dumps(first_nft.__dict__, indent=2, default=str)[:500])
            else:
                print(str(first_nft)[:500])
    else:
        print("⚠️  Result is None or empty")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

# Print curl command
print("\n" + "=" * 70)
print("📝 EQUIVALENT CURL COMMAND:")
print("=" * 70)

# Ankr Advanced API endpoint format
endpoint = f"https://rpc.ankr.com/multichain/{api_key}"

curl_command = f"""curl -X POST {endpoint} \\
  -H "Content-Type: application/json" \\
  -d '{{
    "jsonrpc": "2.0",
    "method": "ankr_getNFTsByOwner",
    "params": {{
      "walletAddress": "{wallet_address}",
      "blockchain": "{blockchain}",
      "pageSize": {page_size}
    }},
    "id": 1
  }}'"""

print(curl_command)
