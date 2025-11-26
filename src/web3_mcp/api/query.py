"""
Query API implementation for Ankr Advanced API
"""

import asyncio
from typing import Any, Dict, List, Optional

from ankr import AnkrWeb3
from pydantic import BaseModel

from ..constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..utils import extract_paginated_result, to_serializable


class BlockchainStatsRequest(BaseModel):
    blockchain: str


class BlocksRequest(BaseModel):
    blockchain: str
    from_block: Optional[int] = None
    to_block: Optional[int] = None
    descending_order: Optional[bool] = None
    page_token: Optional[str] = None
    page_size: Optional[int] = DEFAULT_PAGE_SIZE


class LogsRequest(BaseModel):
    blockchain: str
    from_block: Optional[int] = None
    to_block: Optional[int] = None
    address: Optional[str] = None
    topics: Optional[List[str]] = None
    descending_order: Optional[bool] = None
    page_token: Optional[str] = None
    page_size: Optional[int] = DEFAULT_PAGE_SIZE


class TransactionsByHashRequest(BaseModel):
    blockchain: str
    transaction_hash: str


class TransactionsByAddressRequest(BaseModel):
    blockchain: str
    wallet_address: str
    from_block: Optional[int] = None
    to_block: Optional[int] = None
    descending_order: Optional[bool] = None
    page_token: Optional[str] = None
    page_size: Optional[int] = DEFAULT_PAGE_SIZE


class InteractionsRequest(BaseModel):
    blockchain: str
    wallet_address: str
    from_block: Optional[int] = None
    to_block: Optional[int] = None
    contract_address: Optional[str] = None
    descending_order: Optional[bool] = None
    page_token: Optional[str] = None
    page_size: Optional[int] = DEFAULT_PAGE_SIZE


class QueryApi:
    """Wrapper for Ankr Query API methods"""

    def __init__(self, client: AnkrWeb3):
        self.client = client

    async def get_blockchain_stats(self, request: BlockchainStatsRequest) -> Dict[str, Any]:
        """Get blockchain statistics"""
        from ankr.types import GetBlockchainStatsRequest

        ankr_request = GetBlockchainStatsRequest(blockchain=request.blockchain)

        result = self.client.query.get_blockchain_stats(ankr_request)

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

        params = {"blockchain": request.blockchain}

        if request.from_block is not None:
            params["fromBlock"] = str(request.from_block)

        if request.to_block is not None:
            params["toBlock"] = str(request.to_block)

        if request.descending_order is not None:
            params["descOrder"] = str(request.descending_order).lower()

        ankr_request = GetBlocksRequest(**params)

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

        ankr_request = GetLogsRequest(
            blockchain=request.blockchain,
            fromBlock=request.from_block,
            toBlock=request.to_block,
            address=request.address,
            topics=request.topics,
            descOrder=request.descending_order,
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
                address=request.wallet_address,
                fromBlock=request.from_block,
                toBlock=request.to_block,
                descOrder=request.descending_order,
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

        # GetInteractionsRequest only has 'address' and 'syncCheck'
        ankr_request = GetInteractionsRequest(
            address=request.wallet_address,
            syncCheck=None,
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
