"""
MCP server implementation for Ankr Advanced API
"""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .api.nft import (
    NFTApi,
    NFTByOwnerRequest,
    NFTHoldersRequest,
    NFTMetadataRequest,
    NFTTransfersRequest,
)
from .api.query import (
    BlockchainStatsRequest,
    BlocksRequest,
    InteractionsRequest,
    LogsRequest,
    QueryApi,
    TransactionsByAddressRequest,
    TransactionsByHashRequest,
)
from .api.token import (
    AccountBalanceRequest,
    CurrenciesRequest,
    CurrenciesResponse,
    TokenApi,
    TokenHoldersCountRequest,
    TokenHoldersCountResponse,
    TokenHoldersRequest,
    TokenHoldersResponse,
    TokenPriceRequest,
    TokenTransfersRequest,
    TokenTransfersResponse,
)
from .auth import AnkrAuth
from .constants import SUPPORTED_NETWORKS

# Initialize authentication
_auth = None


def init_server(
    name: str = "Ankr MCP", endpoint: Optional[str] = None, private_key: Optional[str] = None
) -> FastMCP:
    """
    Initialize the MCP server

    Args:
        name: Server name
        endpoint: Ankr RPC endpoint (defaults to ANKR_ENDPOINT env var)
        private_key: Private key for authentication (defaults to ANKR_PRIVATE_KEY env var)

    Returns:
        Initialized FastMCP server instance
    """
    global _auth

    # Initialize authentication
    _auth = AnkrAuth(endpoint, private_key)

    # Create MCP server
    mcp: FastMCP = FastMCP(name, dependencies=["ankr-sdk>=1.0.2"])

    # Initialize API clients
    nft_api = NFTApi(_auth.client)
    query_api = QueryApi(_auth.client)
    token_api = TokenApi(_auth.client)

    @mcp.tool()
    async def get_nfts_by_owner(request: NFTByOwnerRequest) -> Dict[str, Any]:
        """
        Retrieve all NFTs (Non-Fungible Tokens) owned by a specific wallet address.

        Use this tool to get a complete list of NFTs in a wallet, including ERC-721 and ERC-1155 tokens.
        Returns NFT metadata such as name, image, collection information, and token IDs. Supports filtering
        by blockchain and pagination for wallets with many NFTs.

        Args:
            request: Request containing wallet address, optional blockchain filter, and pagination parameters

        Returns:
            Dictionary containing "assets" array with NFT details (name, image, collection, tokenId, etc.) and "next_page_token" for pagination
        """
        return await nft_api.get_nfts_by_owner(request)

    @mcp.tool()
    async def get_nft_metadata(request: NFTMetadataRequest) -> Dict[str, Any]:
        """
        Retrieve detailed metadata for a specific NFT by contract address and token ID.

        Use this tool to get complete NFT information including name, description, image URL, attributes/traits,
        and other metadata stored on-chain or in IPFS. Essential for displaying NFT details or verifying
        NFT properties.

        Args:
            request: Request containing blockchain identifier, NFT contract address, and token ID

        Returns:
            Dictionary containing NFT metadata including name, description, image, attributes, and contract information
        """
        return await nft_api.get_nft_metadata(request)

    @mcp.tool()
    async def get_nft_holders(request: NFTHoldersRequest) -> Dict[str, Any]:
        """
        Retrieve list of wallet addresses that hold NFTs from a specific collection.

        Use this tool to get all current holders of an NFT collection. Useful for analyzing collection distribution,
        identifying whale holders, or building holder lists for airdrops. Supports pagination for large collections.

        Args:
            request: Request containing blockchain identifier, NFT collection contract address, and pagination parameters

        Returns:
            Dictionary containing "holders" array with wallet addresses and "next_page_token" for pagination
        """
        return await nft_api.get_nft_holders(request)

    @mcp.tool()
    async def get_nft_transfers(request: NFTTransfersRequest) -> Dict[str, Any]:
        """
        Retrieve transfer history for NFTs, filtered by collection, token, wallet, or block range.

        Use this tool to track NFT movements, analyze trading activity, or build transfer history views.
        Can filter by contract address, specific token ID, wallet address (sender or receiver), and block range.
        Supports pagination for large result sets.

        Args:
            request: Request containing blockchain identifier, optional filters (contract_address, token_id, wallet_address,
                    from_block, to_block), and pagination parameters

        Returns:
            Dictionary containing "transfers" array with transfer details (from, to, tokenId, block info) and "next_page_token" for pagination
        """
        return await nft_api.get_nft_transfers(request)

    @mcp.tool()
    async def get_blockchain_stats(request: BlockchainStatsRequest) -> Dict[str, Any]:
        """
        Retrieve blockchain statistics including latest block number, total transaction count, and transactions per second (TPS).

        Use this tool to get an overview of blockchain activity and current state. Returns statistics such as:
        - Latest block number
        - Total number of transactions
        - Current transactions per second (TPS)

        Args:
            request: Request containing the blockchain identifier (e.g., "eth", "bsc", "polygon")

        Returns:
            Dictionary containing "stats" with lastBlockNumber, transactions, and tps fields
        """
        return await query_api.get_blockchain_stats(request)

    @mcp.tool()
    async def get_blocks(request: BlocksRequest) -> Dict[str, Any]:
        """
        Retrieve blockchain block information within a specified range.

        Use this tool to fetch block data including block number, hash, timestamp, transaction count, gas used, and other block metadata.
        Supports filtering by block range (from_block to to_block) and pagination for large result sets.

        Args:
            request: Request containing blockchain identifier, optional block range (from_block, to_block),
                    sort order (descending_order), and pagination parameters (page_token, page_size)

        Returns:
            Dictionary containing "blocks" array with block data and "next_page_token" for pagination
        """
        return await query_api.get_blocks(request)

    @mcp.tool()
    async def get_logs(request: LogsRequest) -> Dict[str, Any]:
        """
        Retrieve blockchain event logs emitted by smart contracts.

        Use this tool to query event logs filtered by contract address, topics (event signatures), and block range.
        Useful for tracking contract events, token transfers, or other on-chain activities. Supports pagination
        for large result sets.

        Args:
            request: Request containing blockchain identifier, optional filters (address, topics, from_block, to_block),
                    sort order (descending_order), and pagination parameters (page_token, page_size)

        Returns:
            Dictionary containing "logs" array with log entries (address, topics, data, block info) and "next_page_token" for pagination
        """
        return await query_api.get_logs(request)

    @mcp.tool()
    async def get_transactions_by_hash(request: TransactionsByHashRequest) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific transaction by its hash.

        Use this tool to get complete transaction details including sender, recipient, value, gas information,
        transaction status, block information, and input data. Essential for verifying transaction status
        and examining transaction details.

        Args:
            request: Request containing blockchain identifier and transaction hash

        Returns:
            Dictionary containing complete transaction details including hash, from, to, value, gas, status, block info, and logs
        """
        return await query_api.get_transactions_by_hash(request)

    @mcp.tool()
    async def get_transactions_by_address(request: TransactionsByAddressRequest) -> Dict[str, Any]:
        """
        Retrieve all transactions associated with a wallet or contract address.

        Use this tool to get transaction history for a specific address. Can filter by block range and supports
        pagination. Returns both incoming and outgoing transactions. Useful for tracking wallet activity,
        analyzing contract interactions, or building transaction history views.

        Args:
            request: Request containing blockchain identifier, wallet/contract address, optional block range filters,
                    sort order (descending_order), and pagination parameters (page_token, page_size)

        Returns:
            Dictionary containing "transactions" array with transaction details and "next_page_token" for pagination
        """
        return await query_api.get_transactions_by_address(request)

    @mcp.tool()
    async def get_interactions(request: InteractionsRequest) -> Dict[str, Any]:
        """
        Retrieve list of blockchains where a wallet or contract address has had interactions.

        Use this tool to discover which blockchains an address has been active on. An interaction is defined as
        having tokens, NFTs, or transactions on a blockchain. Useful for multi-chain wallet analysis or
        determining which chains to query for a specific address.

        Args:
            request: Request containing blockchain identifier and wallet/contract address

        Returns:
            Dictionary containing "interactions" array with blockchain identifiers where the address has activity
        """
        return await query_api.get_interactions(request)

    @mcp.tool()
    async def get_account_balance(request: AccountBalanceRequest) -> Dict[str, Any]:
        """
        Retrieve token balances for a wallet address, including native tokens and ERC-20 tokens.

        Use this tool to get a complete overview of all tokens held by a wallet. Returns balances in both
        raw token amounts and USD values. Can filter to show only ERC-20 tokens, only native tokens, or
        exclude NFTs. Supports pagination for wallets with many token holdings.

        Args:
            request: Request containing wallet address, optional blockchain filter, filter options (erc20_only,
                    native_only, tokens_only), and pagination parameters

        Returns:
            Dictionary containing "assets" array with token balances (symbol, balance, balanceUsd, decimals, etc.) and "next_page_token" for pagination
        """
        return await token_api.get_account_balance(request)

    @mcp.tool()
    async def get_currencies(request: CurrenciesRequest) -> CurrenciesResponse:
        """
        Retrieve list of available currencies/tokens on a blockchain.

        Use this tool to discover what tokens are available on a specific blockchain. Returns token information
        including contract addresses, symbols, names, and decimals. Useful for building token selection interfaces
        or discovering available tokens on a chain.

        Args:
            request: Request containing optional blockchain filter and pagination parameters

        Returns:
            Dictionary containing "currencies" array with token information (address, symbol, name, decimals, etc.)
        """
        return await token_api.get_currencies(request)

    @mcp.tool()
    async def get_token_price(request: TokenPriceRequest) -> Dict[str, Any]:
        """
        Retrieve current price information for a specific token in USD.

        Use this tool to get real-time token prices. Returns the current USD price of the token, useful for
        calculating portfolio values, displaying prices, or performing price-based calculations.

        Args:
            request: Request containing blockchain identifier and token contract address

        Returns:
            Dictionary containing "price_usd" with the current token price in USD
        """
        return await token_api.get_token_price(request)

    @mcp.tool()
    async def get_token_holders(request: TokenHoldersRequest) -> TokenHoldersResponse:
        """
        Retrieve list of wallet addresses that hold a specific token.

        Use this tool to get all current holders of a token. Useful for analyzing token distribution,
        identifying large holders, or building holder lists. Supports pagination for tokens with many holders.

        Args:
            request: Request containing blockchain identifier, token contract address, and pagination parameters

        Returns:
            Dictionary containing "holders" array with wallet addresses and their balances, and "next_page_token" for pagination
        """
        return await token_api.get_token_holders(request)

    @mcp.tool()
    async def get_token_holders_count(
        request: TokenHoldersCountRequest,
    ) -> TokenHoldersCountResponse:
        """
        Retrieve the total number of unique addresses holding a specific token.

        Use this tool to quickly get the holder count for a token without fetching the full list of holders.
        Useful for displaying token statistics or determining token distribution metrics.

        Args:
            request: Request containing blockchain identifier and token contract address

        Returns:
            Dictionary containing "holders_count" with the total number of unique token holders
        """
        return await token_api.get_token_holders_count(request)

    @mcp.tool()
    async def get_token_transfers(request: TokenTransfersRequest) -> TokenTransfersResponse:
        """
        Retrieve transfer history for tokens, filtered by contract, wallet, or block range.

        Use this tool to track token movements, analyze trading activity, or build transfer history views.
        Can filter by token contract address, wallet address (sender or receiver), and block range.
        Supports pagination for large result sets.

        Args:
            request: Request containing blockchain identifier, optional filters (contract_address, wallet_address,
                    from_block, to_block), and pagination parameters

        Returns:
            Dictionary containing "transfers" array with transfer details (from, to, value, block info) and "next_page_token" for pagination
        """
        return await token_api.get_token_transfers(request)

    @mcp.tool()
    def get_supported_networks() -> List[str]:
        """
        Retrieve list of blockchain networks supported by this MCP server.

        Use this tool to discover which blockchains are available for querying. Returns a list of blockchain
        identifiers (e.g., "eth", "bsc", "polygon") that can be used in other tool requests.

        Returns:
            List of supported blockchain network identifiers (e.g., ["eth", "bsc", "polygon", "avalanche", "arbitrum", "fantom", "optimism"])
        """
        return SUPPORTED_NETWORKS

    @mcp.resource("ankr://info")
    def get_ankr_info() -> Dict[str, Any]:
        """
        Get information about Ankr Advanced API

        Returns:
            Information about the Ankr Advanced API
        """
        return {
            "name": "Ankr Advanced API",
            "description": "Multi-chain Web3 data API providing access to NFT, Token and Query data",
            "documentation": "https://www.ankr.com/docs/advanced-api/overview/",
            "supported_networks": SUPPORTED_NETWORKS,
            "api_categories": ["NFT API", "Query API", "Token API"],
        }

    return mcp
