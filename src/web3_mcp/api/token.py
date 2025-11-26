"""
Token API implementation for Ankr Advanced API
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from ankr import AnkrWeb3
from pydantic import BaseModel, Field

from ..constants import DEFAULT_CURRENCIES_LIMIT, DEFAULT_PAGE_SIZE, MAX_CURRENCIES_LIMIT, MAX_PAGE_SIZE
from ..utils import extract_paginated_result, to_serializable


class AccountBalanceRequest(BaseModel):
    """Request model for getting token balances"""

    wallet_address: str = Field(..., description="Wallet address to query token balances for (hex string, e.g., '0x...')")
    blockchain: Optional[str] = Field(
        None,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc. If not specified, queries all supported chains.",
    )
    page_size: Optional[int] = Field(None, description="Number of token balances per page (max 100)")
    page_token: Optional[str] = Field(None, description="Token from previous response to fetch the next page of results")
    erc20_only: Optional[bool] = Field(None, description="If true, return only ERC-20 tokens (exclude native tokens)")
    native_only: Optional[bool] = Field(None, description="If true, return only native blockchain tokens (e.g., ETH, BNB)")
    tokens_only: Optional[bool] = Field(None, description="If true, return only tokens (exclude NFTs)")


class CurrenciesRequest(BaseModel):
    """Request model for getting available currencies on a blockchain"""

    blockchain: Optional[str] = Field(
        None,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc. If not specified, returns currencies from all chains.",
    )
    page_token: Optional[str] = Field(None, description="Token from previous response to fetch the next page of results")
    page_size: Optional[int] = Field(DEFAULT_PAGE_SIZE, description="Number of currencies per page (max 50)")


class TokenPriceRequest(BaseModel):
    """Request model for getting token price information"""

    blockchain: str = Field(
        ...,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    contract_address: str = Field(..., description="Token contract address (hex string, e.g., '0x...')")


# Not provided as a tool, but needed for internal functionality
class TokenHoldersRequest(BaseModel):
    """Request model for getting token holders"""

    blockchain: str = Field(
        ...,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    contract_address: str = Field(..., description="Token contract address (hex string, e.g., '0x...')")
    page_token: Optional[str] = Field(None, description="Token from previous response to fetch the next page of results")
    page_size: Optional[int] = Field(DEFAULT_PAGE_SIZE, description="Number of holders per page (max 100)")


class TokenHoldersCountRequest(BaseModel):
    """Request model for getting token holders count"""

    blockchain: str = Field(
        ...,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    contract_address: str = Field(..., description="Token contract address (hex string, e.g., '0x...')")


class TokenTransfersRequest(BaseModel):
    """Request model for getting token transfer history"""

    blockchain: str = Field(
        ...,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    contract_address: Optional[str] = Field(None, description="Token contract address to filter transfers by (hex string, e.g., '0x...')")
    wallet_address: Optional[str] = Field(None, description="Wallet address to filter transfers by (hex string, e.g., '0x...')")
    from_block: Optional[int] = Field(
        None, description="Block number to start from (inclusive, >= 0). Supported formats: hex, decimal, 'earliest', 'latest'"
    )
    to_block: Optional[int] = Field(
        None, description="Block number to end with (inclusive, >= 0). Supported formats: hex, decimal, 'earliest', 'latest'"
    )
    page_token: Optional[str] = Field(None, description="Token from previous response to fetch the next page of results")
    page_size: Optional[int] = Field(DEFAULT_PAGE_SIZE, description="Number of transfers per page (max 100)")


class AccountBalanceResponse(BaseModel):
    balances: List[Dict[str, Any]]
    next_page_token: str = ""


class CurrenciesResponse(BaseModel):
    currencies: List[Dict[str, Any]]


class TokenPriceResponse(BaseModel):
    prices: List[Dict[str, Any]]


# Not provided as a tool, but needed for internal functionality
class TokenHoldersResponse(BaseModel):
    holders: List[Dict[str, Any]]
    next_page_token: str = ""


class TokenHoldersCountResponse(BaseModel):
    count: int


class TokenTransfersResponse(BaseModel):
    transfers: List[Dict[str, Any]]
    next_page_token: str = ""


class TokenApi:
    """Wrapper for Ankr Token API methods"""

    def __init__(self, client: AnkrWeb3):
        self.client = client

    async def get_account_balance(self, request: AccountBalanceRequest) -> Dict[str, Any]:
        """Get token balances for a wallet address"""
        from ankr.types import GetAccountBalanceRequest

        ankr_request = GetAccountBalanceRequest(
            walletAddress=request.wallet_address,
            blockchain=request.blockchain,
            pageToken=request.page_token,
            pageSize=request.page_size,
        )

        result = self.client.token.get_account_balance(ankr_request)
        balances = [to_serializable(balance) for balance in result] if result else []
        return {"assets": balances}

    async def get_currencies(self, request: CurrenciesRequest) -> CurrenciesResponse:
        """Get available currencies"""
        from ankr.types import GetCurrenciesRequest

        ankr_request = GetCurrenciesRequest(
            blockchain=request.blockchain if request.blockchain else None,
        )

        # Check if Ankr SDK supports pagination for get_currencies
        # Note: Ankr SDK may not support page_size/page_token for get_currencies
        # If it does, we can add:
        # if request.page_size is not None:
        #     ankr_request.pageSize = request.page_size
        # if request.page_token:
        #     ankr_request.pageToken = request.page_token

        result = self.client.token.get_currencies(ankr_request)
        currencies_raw = list(result) if result else []

        # Apply page_size limit (client-side limit)
        limit = min(request.page_size or DEFAULT_CURRENCIES_LIMIT, MAX_CURRENCIES_LIMIT)
        if len(currencies_raw) > limit:
            currencies_raw = currencies_raw[:limit]

        # Convert objects to dicts for Pydantic validation
        currencies = [to_serializable(c) for c in currencies_raw]
        return CurrenciesResponse(currencies=currencies)

    async def get_token_price(self, request: TokenPriceRequest) -> Dict[str, Any]:
        """Get token price information"""
        from ankr.types import GetTokenPriceRequest

        ankr_request = GetTokenPriceRequest(
            blockchain=request.blockchain,
            contractAddress=request.contract_address,
        )

        result = self.client.token.get_token_price(ankr_request)

        # get_token_price returns string (usdPrice) directly
        if result is None:
            raise ValueError("Failed to get token price: result is None")

        # If result is a string, it's the direct price value
        if isinstance(result, str):
            # Handle empty string or "0"
            if not result or result.strip() == "":
                return {"price_usd": "0"}
            try:
                price = float(result)
                return {"price_usd": result}
            except ValueError:
                # If it's not a valid number, try to parse as JSON
                try:
                    data = json.loads(result)
                    if isinstance(data, dict) and "usdPrice" in data:
                        return {"price_usd": str(data["usdPrice"])}
                    elif isinstance(data, dict) and "price" in data:
                        return {"price_usd": str(data["price"])}
                    elif isinstance(data, dict) and "price_usd" in data:
                        return {"price_usd": str(data["price_usd"])}
                except json.JSONDecodeError:
                    pass
                # If all parsing fails, return the string as-is
                return {"price_usd": result}

        # Try to get price from object attributes
        price_value: Optional[float] = None
        if hasattr(result, "usdPrice"):
            price_value = float(result.usdPrice) if result.usdPrice else 0
        elif hasattr(result, "price"):
            price_value = float(result.price) if result.price else 0
        elif hasattr(result, "price_usd"):
            price_value = float(result.price_usd) if result.price_usd else 0

        if price_value is None:
            raise ValueError("Failed to get token price: price not found in response")

        return {"price_usd": str(price_value)}

    # Not provided as a tool, but needed for internal functionality
    async def get_token_holders(self, request: TokenHoldersRequest) -> TokenHoldersResponse:
        """Get token holders"""
        from ankr.types import GetTokenHoldersRequest

        ankr_request = GetTokenHoldersRequest(
            blockchain=request.blockchain,
            contractAddress=request.contract_address,
            pageToken=request.page_token,
            pageSize=request.page_size,
        )

        # Run in executor to avoid blocking event loop
        def _get_and_convert_holders():
            """Get holders and convert generator to list in executor"""
            try:
                result = self.client.token.get_token_holders(ankr_request)
                return extract_paginated_result(
                    result, "holders", request.page_size, MAX_PAGE_SIZE
                )
            except Exception:
                return None, []

        loop = asyncio.get_event_loop()
        next_token, holders = await loop.run_in_executor(None, _get_and_convert_holders)

        if holders is None:
            return TokenHoldersResponse(holders=[], next_page_token="")

        # Convert to serializable format
        holders_list = [to_serializable(h) for h in holders]
        return TokenHoldersResponse(holders=holders_list, next_page_token=next_token or "")

    async def get_token_holders_count(
        self, request: TokenHoldersCountRequest
    ) -> TokenHoldersCountResponse:
        """Get token holders count"""
        from ankr.types import GetTokenHoldersCountRequest

        ankr_request = GetTokenHoldersCountRequest(
            blockchain=request.blockchain,
            contractAddress=request.contract_address,
        )

        result = self.client.token.get_token_holders_count(ankr_request)
        count = result.count if hasattr(result, "count") else 0
        return TokenHoldersCountResponse(count=count)

    async def get_token_transfers(self, request: TokenTransfersRequest) -> TokenTransfersResponse:
        """Get token transfers"""
        from ankr.types import GetTransfersRequest

        # GetTransfersRequest uses 'address' for contract or wallet address
        address = request.contract_address or request.wallet_address
        addresses = [address] if address else None

        ankr_request = GetTransfersRequest(
            blockchain=request.blockchain,
            address=addresses,
            fromBlock=request.from_block,
            toBlock=request.to_block,
            pageToken=request.page_token,
            pageSize=request.page_size,
        )

        # Run in executor to avoid blocking event loop
        def _get_and_convert_transfers():
            """Get transfers and convert generator to list in executor"""
            try:
                result = self.client.token.get_token_transfers(ankr_request)
                return extract_paginated_result(
                    result, "transfers", request.page_size, MAX_PAGE_SIZE
                )
            except Exception:
                return None, []

        loop = asyncio.get_event_loop()
        next_token, transfers = await loop.run_in_executor(None, _get_and_convert_transfers)

        if transfers is None:
            return TokenTransfersResponse(transfers=[], next_page_token="")

        # Convert to serializable format
        transfers_list = [to_serializable(t) for t in transfers]
        return TokenTransfersResponse(transfers=transfers_list, next_page_token=next_token or "")
