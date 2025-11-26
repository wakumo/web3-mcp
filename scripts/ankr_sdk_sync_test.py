#!/usr/bin/env python3
"""Test Ankr SDK directly to see response format and timing"""

import os
import sys
import time
import json

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from ankr import AnkrWeb3
from ankr.types import GetNFTsByOwnerRequest

api_key = os.environ.get("ANKR_PRIVATE_KEY") or os.environ.get("ANKR_API_KEY")
if not api_key:
    print("❌ Need ANKR_PRIVATE_KEY")
    sys.exit(1)

print("=" * 70)
print("TEST ANKR SDK DIRECTLY (SYNC)")
print("=" * 70)

client = AnkrWeb3(api_key=api_key)

wallet = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
request = GetNFTsByOwnerRequest(
    walletAddress=wallet,
    blockchain="eth",
    pageSize=5
)

print(f"\n📋 Calling client.nft.get_nfts()...")
print(f"   Wallet: {wallet}")
print(f"   Blockchain: eth")
print(f"   PageSize: 5")

start_time = time.time()
try:
    result = client.nft.get_nfts(request)
    elapsed = time.time() - start_time
    print(f"\n✅ Call completed in {elapsed:.2f} seconds")
    print(f"📊 Result type: {type(result)}")
    print(f"📊 Result: {result}")

    # Check attributes
    if hasattr(result, "__dict__"):
        print(f"\n📋 Result attributes: {list(result.__dict__.keys())}")
        if hasattr(result, "assets"):
            print(f"   - assets type: {type(result.assets)}")
            print(f"   - assets length: {len(result.assets) if hasattr(result.assets, '__len__') else 'N/A'}")
            if result.assets and len(result.assets) > 0:
                print(f"   - First asset type: {type(result.assets[0])}")
                if hasattr(result.assets[0], "__dict__"):
                    print(f"   - First asset keys: {list(result.assets[0].__dict__.keys())[:5]}")

    # Try to serialize
    print(f"\n🔄 Testing serialization...")
    try:
        if hasattr(result, "assets"):
            assets = result.assets
            assets_list = []
            for i, asset in enumerate(assets):
                if hasattr(asset, "__dict__"):
                    asset_dict = {}
                    for key, value in asset.__dict__.items():
                        if hasattr(value, "__dict__"):
                            asset_dict[key] = value.__dict__
                        elif isinstance(value, list):
                            asset_dict[key] = [
                                item.__dict__ if hasattr(item, "__dict__") else item
                                for item in value
                            ]
                        else:
                            asset_dict[key] = value
                    assets_list.append(asset_dict)
                else:
                    assets_list.append(str(asset))
                if i >= 0:  # Just first one for testing
                    print(f"   Serialized first asset: {json.dumps(assets_list[0], indent=2, default=str)[:200]}")
                    break
        print(f"✅ Serialization test passed")
    except Exception as e:
        print(f"❌ Serialization error: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    elapsed = time.time() - start_time
    print(f"\n❌ Error after {elapsed:.2f} seconds: {e}")
    import traceback
    traceback.print_exc()
