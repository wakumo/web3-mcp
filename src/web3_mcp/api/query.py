"""
Query API implementation for Ankr Advanced API
"""

import asyncio
from typing import Any, Dict, List, Optional, Union

from ankr import AnkrWeb3
from pydantic import BaseModel, Field, field_validator

from ..constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, SUPPORTED_NETWORKS
from ..utils import extract_paginated_result, to_serializable

BlockIdentifier = Union[int, float, str]
BlockchainIdentifier = Union[str, List[str]]
LogTopic = Union[str, List[str]]


class BlockchainStatsRequest(BaseModel):
    """Request model for getting blockchain statistics"""

    blockchain: BlockchainIdentifier = Field(
        ...,
        description="Chain or chains to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism.",
    )
    sync_check: Optional[bool] = Field(None, description="If true, include API sync status checks")

    @field_validator("blockchain")
    @classmethod
    def validate_supported_blockchains(cls, value: BlockchainIdentifier) -> BlockchainIdentifier:
        blockchains = [value] if isinstance(value, str) else value
        unsupported = [blockchain for blockchain in blockchains if blockchain not in SUPPORTED_NETWORKS]
        if unsupported:
            supported = ", ".join(SUPPORTED_NETWORKS)
            invalid = ", ".join(unsupported)
            raise ValueError(
                f"Unsupported blockchain for get_blockchain_stats: {invalid}. "
                f"Supported values: {supported}."
            )
        return value


class BlocksRequest(BaseModel):
    """Request model for getting blocks within a specified range"""

    blockchain: str = Field(
        ...,
        description="Chain to query: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    from_block: Optional[BlockIdentifier] = Field(
        None, description="Block number to start from (inclusive, >= 0). Supports integers, decimals, 'earliest', and 'latest'."
    )
    to_block: Optional[BlockIdentifier] = Field(
        None, description="Block number to end with (inclusive, >= 0). Supports integers, decimals, 'earliest', and 'latest'."
    )
    descending_order: Optional[bool] = Field(None, description="True for descending order (newest first), false for ascending order (oldest first)")
    include_logs: Optional[bool] = Field(None, description="If true, include block logs in the response")
    include_txs: Optional[bool] = Field(None, description="If true, include block transactions in the response")
    decode_logs: Optional[bool] = Field(None, description="If true, decode logs when included")
    decode_tx_data: Optional[bool] = Field(None, description="If true, decode transaction input data when transactions are included")
    sync_check: Optional[bool] = Field(None, description="If true, include API sync status checks")


class LogsRequest(BaseModel):
    """Request model for getting blockchain event logs"""

    blockchain: BlockchainIdentifier = Field(
        ...,
        description="Chain or chains to query. Supported values include eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    from_block: Optional[BlockIdentifier] = Field(
        None, description="Block number to start from (inclusive, >= 0). Supports integers, decimals, 'earliest', and 'latest'."
    )
    to_block: Optional[BlockIdentifier] = Field(
        None, description="Block number to end with (inclusive, >= 0). Supports integers, decimals, 'earliest', and 'latest'."
    )
    from_timestamp: Optional[BlockIdentifier] = Field(None, description="Start timestamp filter. Supports numeric timestamps, 'earliest', and 'latest'.")
    to_timestamp: Optional[BlockIdentifier] = Field(None, description="End timestamp filter. Supports numeric timestamps, 'earliest', and 'latest'.")
    address: Optional[Union[str, List[str]]] = Field(None, description="Contract address or addresses to filter logs by (hex string, e.g., '0x...')")
    topics: Optional[List[LogTopic]] = Field(
        None, description="Topic filters for logs. Each topic can be a hex string or a list of alternative topic hashes."
    )
    descending_order: Optional[bool] = Field(None, description="True for descending order (newest first), false for ascending order (oldest first)")
    decode_logs: Optional[bool] = Field(None, description="If true, decode matching logs")
    sync_check: Optional[bool] = Field(None, description="If true, include API sync status checks")
    page_token: Optional[str] = Field(None, description="Token from previous response to fetch the next page of results")
    page_size: Optional[int] = Field(DEFAULT_PAGE_SIZE, description="Number of logs per page (max 100)")


class TransactionsByHashRequest(BaseModel):
    """Request model for getting transaction details by hash"""

    blockchain: str = Field(
        ...,
        description="Chain to query. Supported values: eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    transaction_hash: str = Field(..., description="Transaction hash to look up (hex string, e.g., '0x...')")


class TransactionsByAddressRequest(BaseModel):
    """Request model for getting transactions by wallet or contract address"""

    blockchain: BlockchainIdentifier = Field(
        ...,
        description="Chain or chains to query. Supported values include eth, bsc, polygon, avalanche, arbitrum, fantom, optimism, base, linea, scroll, etc.",
    )
    wallet_address: str = Field(..., description="Wallet or contract address to search for transactions (hex string, e.g., '0x...')")
    from_block: Optional[BlockIdentifier] = Field(
        None, description="Block number to start from (inclusive, >= 0). Supports integers, decimals, 'earliest', and 'latest'."
    )
    to_block: Optional[BlockIdentifier] = Field(
        None, description="Block number to end with (inclusive, >= 0). Supports integers, decimals, 'earliest', and 'latest'."
    )
    from_timestamp: Optional[BlockIdentifier] = Field(None, description="Start timestamp filter. Supports numeric timestamps, 'earliest', and 'latest'.")
    to_timestamp: Optional[BlockIdentifier] = Field(None, description="End timestamp filter. Supports numeric timestamps, 'earliest', and 'latest'.")
    descending_order: Optional[bool] = Field(None, description="True for descending order (newest first), false for ascending order (oldest first)")
    include_logs: Optional[bool] = Field(None, description="If true, include transaction logs in the response")
    sync_check: Optional[bool] = Field(None, description="If true, include API sync status checks")
    page_token: Optional[str] = Field(None, description="Token from previous response to fetch the next page of results")
    page_size: Optional[int] = Field(DEFAULT_PAGE_SIZE, description="Number of transactions per page (max 100)")


class InteractionsRequest(BaseModel):
    """Request model for getting blockchains interacted with a particular address"""

    wallet_address: str = Field(..., description="Wallet or contract address to check for interactions (hex string, e.g., '0x...')")
    sync_check: Optional[bool] = Field(None, description="If true, include API sync status checks")


class QueryApi:
    """Wrapper for Ankr Query API methods"""

    def __init__(self, client: AnkrWeb3):
        self.client = client

    async def get_blockchain_stats(self, request: BlockchainStatsRequest) -> Dict[str, Any]:
        """Get blockchain statistics"""
        from ankr.types import GetBlockchainStatsRequest

        ankr_request = GetBlockchainStatsRequest(
            blockchain=request.blockchain,
            syncCheck=request.sync_check,
        )

        try:
            result = self.client.query.get_blockchain_stats(ankr_request)
        except Exception as exc:
            if "restricted by blockchain schema" in str(exc):
                raise RuntimeError(
                    "Ankr rejected ankr_getBlockchainStats for the requested blockchain schema. "
                    "The request shape is valid; verify that this Ankr API key/project has "
                    "Advanced API multichain access and getBlockchainStats enabled for "
                    f"blockchain={request.blockchain!r}."
                ) from exc
            raise

        if isinstance(result, list) and len(result) > 0:
            stats_obj = result[0]
            stats = {
                "lastBlockNumber": getattr(stats_obj, "latestBlockNumber", getattr(stats_obj, "lastBlockNumber", 0)),
                "transactions": getattr(stats_obj, "totalTransactionsCount", getattr(stats_obj, "transactions", 0)),
                "tps": getattr(stats_obj, "tps", 0),
            }
            return {"stats": stats}

        if hasattr(result, "__dict__"):
            return {"stats": result.__dict__}

        stats = {
            "lastBlockNumber": getattr(result, "lastBlockNumber", getattr(result, "latestBlockNumber", 0)),
            "transactions": getattr(result, "transactions", getattr(result, "totalTransactionsCount", 0)),
            "tps": getattr(result, "tps", 0),
        }
        return {"stats": stats}

    async def get_blocks(self, request: BlocksRequest) -> Dict[str, Any]:
        """Get blocks information"""
        from ankr.types import GetBlocksRequest

        params = {
            "blockchain": request.blockchain,
            "fromBlock": request.from_block,
            "toBlock": request.to_block,
            "descOrder": request.descending_order,
            "includeLogs": request.include_logs,
            "includeTxs": request.include_txs,
            "decodeLogs": request.decode_logs,
            "decodeTxData": request.decode_tx_data,
            "syncCheck": request.sync_check,
        }
        ankr_request = GetBlocksRequest(
            **{key: value for key, value in params.items() if value is not None}
        )

        result = self.client.query.get_blocks(ankr_request)
        if hasattr(result, "__iter__") and not isinstance(result, (str, bytes, dict)):
            blocks = [to_serializable(block) for block in result] if result else []
            return {"blocks": blocks, "next_page_token": ""}
        if result:
            return {"blocks": [to_serializable(result)], "next_page_token": ""}
        return {"blocks": [], "next_page_token": ""}

    async def get_logs(self, request: LogsRequest) -> Dict[str, Any]:
        """Get blockchain logs"""
        from ankr.types import GetLogsRequest

        addresses = [request.address] if isinstance(request.address, str) else request.address
        ankr_request = GetLogsRequest(
            blockchain=request.blockchain,
            fromBlock=request.from_block,
            toBlock=request.to_block,
            fromTimestamp=request.from_timestamp,
            toTimestamp=request.to_timestamp,
            address=addresses,
            topics=request.topics,
            descOrder=request.descending_order,
            decodeLogs=request.decode_logs,
            syncCheck=request.sync_check,
            pageToken=request.page_token,
            pageSize=request.page_size,
        )

        # Run in executor to avoid blocking event loop
        def _get_and_convert_logs():
            """Get logs and convert generator to list in executor"""
            try:
                result = self.client.query.get_logs(ankr_request)
                return extract_paginated_result(
                    result, "logs", request.page_size, MAX_PAGE_SIZE
                )
            except Exception:
                return None, []

        loop = asyncio.get_event_loop()
        next_token, logs = await loop.run_in_executor(None, _get_and_convert_logs)

        if logs is None:
            return {"logs": [], "next_page_token": ""}

        # Convert to serializable format
        logs_list = [to_serializable(log) for log in logs]
        return {"logs": logs_list, "next_page_token": next_token or ""}

    async def get_transactions_by_hash(self, request: TransactionsByHashRequest) -> Dict[str, Any]:
        """Get transactions by hash"""
        from ankr.types import GetTransactionsByHashRequest

        ankr_request = GetTransactionsByHashRequest(
            transactionHash=request.transaction_hash,
            blockchain=request.blockchain,
        )

        result = self.client.query.get_transaction(ankr_request)
        return to_serializable(result)

    async def get_transactions_by_address(
        self, request: TransactionsByAddressRequest
    ) -> Dict[str, Any]:
        """Get transactions by address"""
        from ankr.types import GetTransactionsByAddressRequest

        try:
            ankr_request = GetTransactionsByAddressRequest(
                blockchain=request.blockchain,
                address=[request.wallet_address],
                fromBlock=request.from_block,
                toBlock=request.to_block,
                fromTimestamp=request.from_timestamp,
                toTimestamp=request.to_timestamp,
                descOrder=request.descending_order,
                includeLogs=request.include_logs,
                syncCheck=request.sync_check,
                pageToken=request.page_token,
                pageSize=request.page_size,
            )

            # Run in executor to avoid blocking event loop
            def _get_and_convert_transactions():
                """Get transactions and convert generator to list in executor"""
                try:
                    result = self.client.query.get_transactions_by_address(ankr_request)
                    return extract_paginated_result(
                        result, "transactions", request.page_size, MAX_PAGE_SIZE
                    )
                except Exception:
                    return None, []

            loop = asyncio.get_event_loop()
            next_token, transactions = await loop.run_in_executor(None, _get_and_convert_transactions)

            if transactions is None:
                return {"transactions": [], "next_page_token": ""}

            # Convert to serializable format
            transactions_list = [to_serializable(tx) for tx in transactions]
            return {"transactions": transactions_list, "next_page_token": next_token or ""}

        except Exception:
            return {"transactions": [], "next_page_token": ""}

    async def get_interactions(self, request: InteractionsRequest) -> Dict[str, Any]:
        """Get wallet interactions with contracts"""
        from ankr.types import GetInteractionsRequest

        ankr_request = GetInteractionsRequest(
            address=request.wallet_address,
            syncCheck=request.sync_check,
        )

        # Run in executor to avoid blocking event loop
        def _get_and_convert_interactions():
            """Get interactions and convert to list in executor"""
            try:
                result = self.client.query.get_interactions(ankr_request)

                if result is None:
                    return []

                # get_interactions returns List[Blockchain]
                if isinstance(result, list):
                    return result

                # If result has blockchains attribute
                if hasattr(result, "blockchains"):
                    return result.blockchains if result.blockchains else []

                return []
            except Exception:
                return []

        loop = asyncio.get_event_loop()
        interactions = await loop.run_in_executor(None, _get_and_convert_interactions)

        # Convert to serializable format
        interactions_list = [to_serializable(i) for i in interactions]
        return {"interactions": interactions_list, "next_page_token": ""}
