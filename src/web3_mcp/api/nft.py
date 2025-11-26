"""
NFT API implementation for Ankr Advanced API
"""

import asyncio
from typing import Any, Dict, List, Optional

from ankr import AnkrWeb3
from pydantic import BaseModel, Field

from ..constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..utils import extract_paginated_result, to_serializable


class NFTCollection(BaseModel):
    blockchain: str
    name: str = Field(default="")
    collection_id: str = Field(default="")
    contract_address: str


class NFTMetadata(BaseModel):
    blockchain: str
    contract_address: str
    token_id: str
    token_url: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    attributes: Optional[List[Dict[str, Any]]] = None


class NFTByOwnerRequest(BaseModel):
    """Request model for getting NFTs owned by a wallet address"""

    wallet_address: str = Field(..., description="Wallet address to query NFTs for (hex string, e.g., '0x...')")
    blockchain: Optional[str] = Field(
        None,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc. If not specified, queries all supported chains.",
    )
    page_token: Optional[str] = Field(None, description="Token from previous response to fetch the next page of results")
    page_size: Optional[int] = Field(DEFAULT_PAGE_SIZE, description="Number of NFTs per page (max 100)")


class NFTMetadataRequest(BaseModel):
    """Request model for getting metadata of a specific NFT"""

    blockchain: str = Field(
        ...,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    contract_address: str = Field(..., description="NFT contract address (hex string, e.g., '0x...')")
    token_id: str = Field(..., description="Token ID of the NFT (string, can be a large number for some NFTs)")


class NFTHoldersRequest(BaseModel):
    """Request model for getting holders of an NFT collection"""

    blockchain: str = Field(
        ...,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    contract_address: str = Field(..., description="NFT collection contract address (hex string, e.g., '0x...')")
    page_token: Optional[str] = Field(None, description="Token from previous response to fetch the next page of results")
    page_size: Optional[int] = Field(DEFAULT_PAGE_SIZE, description="Number of holders per page (max 100)")


class NFTTransfersRequest(BaseModel):
    """Request model for getting NFT transfer history"""

    blockchain: str = Field(
        ...,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    contract_address: Optional[str] = Field(None, description="NFT contract address to filter transfers by (hex string, e.g., '0x...')")
    token_id: Optional[str] = Field(None, description="Specific token ID to filter transfers by (string)")
    wallet_address: Optional[str] = Field(None, description="Wallet address to filter transfers by (hex string, e.g., '0x...')")
    from_block: Optional[int] = Field(
        None, description="Block number to start from (inclusive, >= 0). Supported formats: hex, decimal, 'earliest', 'latest'"
    )
    to_block: Optional[int] = Field(
        None, description="Block number to end with (inclusive, >= 0). Supported formats: hex, decimal, 'earliest', 'latest'"
    )
    page_token: Optional[str] = Field(None, description="Token from previous response to fetch the next page of results")
    page_size: Optional[int] = Field(DEFAULT_PAGE_SIZE, description="Number of transfers per page (max 100)")


class NFTApi:
    """Wrapper for Ankr NFT API methods"""

    def __init__(self, client: AnkrWeb3):
        self.client = client

    async def get_nfts_by_owner(self, request: NFTByOwnerRequest) -> Dict[str, Any]:
        """Get NFTs owned by a wallet address"""
        from ankr.types import GetNFTsByOwnerRequest

        try:
            ankr_request = GetNFTsByOwnerRequest(
                walletAddress=request.wallet_address,
                blockchain=request.blockchain if request.blockchain else None,
            )

            if request.page_size is not None:
                ankr_request.pageSize = request.page_size

            if request.page_token:
                ankr_request.pageToken = request.page_token

            # Run both API call and generator conversion in executor to avoid blocking
            def _get_and_convert_nfts():
                """Get NFTs and convert generator to list in executor - safe version"""
                try:
                    result = self.client.nft.get_nfts(ankr_request)
                    return extract_paginated_result(
                        result, "assets", request.page_size, MAX_PAGE_SIZE, alternative_keys=["nfts"]
                    )
                except Exception:
                    return None, []

            loop = asyncio.get_event_loop()
            next_token, assets = await loop.run_in_executor(None, _get_and_convert_nfts)

            if assets is None:
                return {"assets": [], "next_page_token": ""}

            # Convert assets to serializable format
            assets_list = [to_serializable(asset) for asset in assets]
            return {"assets": assets_list, "next_page_token": next_token}

        except Exception:
            return {"assets": [], "next_page_token": ""}

    async def get_nft_metadata(self, request: NFTMetadataRequest) -> Dict[str, Any]:
        """Get metadata for a specific NFT"""
        from ankr.types import GetNFTMetadataRequest

        ankr_request = GetNFTMetadataRequest(
            blockchain=request.blockchain,
            contractAddress=request.contract_address,
            tokenId=request.token_id,
            forceFetch=True,
        )

        result = self.client.nft.get_nft_metadata(ankr_request)
        return to_serializable(result)

    async def get_nft_holders(self, request: NFTHoldersRequest) -> Dict[str, Any]:
        """Get holders of a specific NFT collection"""
        from ankr.types import GetNFTHoldersRequest

        ankr_request = GetNFTHoldersRequest(
            blockchain=request.blockchain,
            contractAddress=request.contract_address,
            pageToken=request.page_token,
            pageSize=request.page_size,
        )

        # Run in executor to avoid blocking event loop
        def _get_and_convert_holders():
            """Get holders and convert generator to list in executor"""
            try:
                result = self.client.nft.get_nft_holders(ankr_request)
                return extract_paginated_result(
                    result, "holders", request.page_size, MAX_PAGE_SIZE
                )
            except Exception:
                return None, []

        loop = asyncio.get_event_loop()
        next_token, holders = await loop.run_in_executor(None, _get_and_convert_holders)

        if holders is None:
            return {"holders": [], "next_page_token": ""}

        # Convert to serializable format
        holders_list = [to_serializable(h) for h in holders]
        return {"holders": holders_list, "next_page_token": next_token or ""}

    async def get_nft_transfers(self, request: NFTTransfersRequest) -> Dict[str, Any]:
        """Get transfer history for NFTs"""
        from ankr.types import GetTransfersRequest

        # GetTransfersRequest.address can be a List[str] - combine contract and wallet addresses
        addresses = []
        if request.contract_address:
            addresses.append(request.contract_address)
        if request.wallet_address:
            addresses.append(request.wallet_address)
        address = addresses if addresses else None

        ankr_request = GetTransfersRequest(
            blockchain=request.blockchain,
            address=address,
            fromBlock=request.from_block,
            toBlock=request.to_block,
            pageToken=request.page_token,
            pageSize=request.page_size,
        )

        # Run in executor to avoid blocking event loop
        def _get_and_convert_transfers():
            """Get transfers and convert generator to list in executor"""
            try:
                result = self.client.nft.get_nft_transfers(ankr_request)
                return extract_paginated_result(
                    result, "transfers", request.page_size, MAX_PAGE_SIZE
                )
            except Exception:
                return None, []

        loop = asyncio.get_event_loop()
        next_token, transfers = await loop.run_in_executor(None, _get_and_convert_transfers)

        if transfers is None:
            return {"transfers": [], "next_page_token": ""}

        # Filter by token_id if provided (client-side filter since API doesn't support it)
        if request.token_id:
            filtered_transfers = []
            for transfer in transfers:
                # Check if transfer has tokenId attribute or in dict
                transfer_token_id = None
                if hasattr(transfer, "tokenId"):
                    transfer_token_id = str(transfer.tokenId)
                elif isinstance(transfer, dict):
                    transfer_token_id = str(transfer.get("tokenId", ""))

                if transfer_token_id and transfer_token_id == str(request.token_id):
                    filtered_transfers.append(transfer)
            transfers = filtered_transfers

        # Convert to serializable format
        transfers_list = [to_serializable(t) for t in transfers]
        return {"transfers": transfers_list, "next_page_token": next_token or ""}
