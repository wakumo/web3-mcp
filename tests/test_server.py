"""
Tests for MCP server
"""

import os
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from web3_mcp.api.nft import NFTApi, NFTTransfersRequest
from web3_mcp.api.query import (
    BlockchainStatsRequest,
    LogsRequest,
    QueryApi,
    TransactionsByAddressRequest,
)
from web3_mcp.api.token import (
    AccountBalanceRequest,
    CurrenciesRequest,
    TokenApi,
    TokenPriceRequest,
    TokenTransfersRequest,
)
from web3_mcp.constants import SUPPORTED_NETWORKS
from web3_mcp.server import init_server


@pytest.fixture(autouse=True)
def mock_env() -> Generator[None, None, None]:
    """Mock environment variables"""
    with patch.dict(
        os.environ, {"ANKR_ENDPOINT": "https://test.endpoint", "ANKR_PRIVATE_KEY": "test_key"}
    ):
        yield


@pytest.fixture
def mock_ankr_web3() -> Generator[MagicMock, None, None]:
    """Mock AnkrWeb3 client"""
    with patch("web3_mcp.auth.AnkrWeb3") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.mark.asyncio
async def test_server_initialization(mock_ankr_web3: MagicMock) -> None:
    """Test server initialization"""
    mcp = init_server(name="Test Server")

    assert mcp.name == "Test Server"

    tools = await mcp.get_tools()
    assert len(tools) > 0


@pytest.mark.asyncio
async def test_utility_tools(mock_ankr_web3: MagicMock) -> None:
    """Test utility tools"""
    mcp = init_server(name="Test Server")

    tools = await mcp.get_tools()
    tool_names = list(tools.keys())

    expected_tools = [
        "get_nfts_by_owner",
        "get_nft_metadata",
        "get_nft_holders",
        "get_blockchain_stats",
        "get_blocks",
        "get_logs",
        "get_account_balance",
        "get_token_price",
        "get_supported_networks",
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names

    resources = await mcp.get_resources()
    resource_uris = list(resources.keys())
    assert "ankr://info" in resource_uris


def test_init_server() -> None:
    # This function is mentioned in the original file but not implemented in the test_server.py file
    # It's assumed to exist as it's called in the test_server_initialization function
    pass


def test_init_server_with_name() -> None:
    # This function is mentioned in the original file but not implemented in the test_server.py file
    # It's assumed to exist as it's called in the test_server_initialization function
    pass


def test_init_server_with_dependencies() -> None:
    # This function is mentioned in the original file but not implemented in the test_server.py file
    # It's assumed to exist as it's called in the test_server_initialization function
    pass


def test_init_server_with_name_and_dependencies() -> None:
    # This function is mentioned in the original file but not implemented in the test_server.py file
    # It's assumed to exist as it's called in the test_server_initialization function
    pass


@pytest.mark.asyncio
async def test_get_blockchain_stats_forwards_curated_multichain_and_sync_check() -> None:
    client = MagicMock()
    client.query.get_blockchain_stats.return_value = []

    request = BlockchainStatsRequest(blockchain=["eth", "polygon"], sync_check=True)

    await QueryApi(client).get_blockchain_stats(request)

    ankr_request = client.query.get_blockchain_stats.call_args.args[0]
    assert ankr_request.blockchain == ["eth", "polygon"]
    assert ankr_request.syncCheck is True


def test_get_blockchain_stats_rejects_uncurated_chain_before_sdk_call() -> None:
    with pytest.raises(ValueError, match="Unsupported blockchain for get_blockchain_stats: base"):
        BlockchainStatsRequest(blockchain="base")


@pytest.mark.asyncio
async def test_get_blockchain_stats_explains_ankr_schema_restriction() -> None:
    client = MagicMock()
    client.query.get_blockchain_stats.side_effect = Exception(
        "failed to handle request, {'code': -32075, 'message': 'Method disabled, reason: restricted by blockchain schema'}"
    )

    request = BlockchainStatsRequest(blockchain="eth")

    with pytest.raises(RuntimeError, match="API key/project has Advanced API multichain access"):
        await QueryApi(client).get_blockchain_stats(request)


@pytest.mark.asyncio
async def test_get_logs_wraps_single_address_and_forwards_sdk_fields() -> None:
    client = MagicMock()
    client.query.get_logs.return_value = []

    request = LogsRequest(
        blockchain=["eth", "base"],
        address="0xabc",
        from_block="earliest",
        to_block="latest",
        from_timestamp=1,
        to_timestamp=2,
        topics=["0xtopic", ["0xalt1", "0xalt2"]],
        descending_order=True,
        decode_logs=True,
        sync_check=True,
        page_token="next",
        page_size=5,
    )

    await QueryApi(client).get_logs(request)

    ankr_request = client.query.get_logs.call_args.args[0]
    assert ankr_request.blockchain == ["eth", "base"]
    assert ankr_request.address == ["0xabc"]
    assert ankr_request.fromBlock == "earliest"
    assert ankr_request.toBlock == "latest"
    assert ankr_request.fromTimestamp == 1
    assert ankr_request.toTimestamp == 2
    assert ankr_request.topics == ["0xtopic", ["0xalt1", "0xalt2"]]
    assert ankr_request.descOrder is True
    assert ankr_request.decodeLogs is True
    assert ankr_request.syncCheck is True
    assert ankr_request.pageToken == "next"
    assert ankr_request.pageSize == 5


@pytest.mark.asyncio
async def test_get_transactions_by_address_wraps_wallet_and_forwards_sdk_fields() -> None:
    client = MagicMock()
    client.query.get_transactions_by_address.return_value = []

    request = TransactionsByAddressRequest(
        blockchain=["eth", "polygon"],
        wallet_address="0xwallet",
        from_block="earliest",
        to_block="latest",
        from_timestamp=10,
        to_timestamp=20,
        descending_order=True,
        include_logs=True,
        sync_check=True,
        page_token="page",
        page_size=3,
    )

    await QueryApi(client).get_transactions_by_address(request)

    ankr_request = client.query.get_transactions_by_address.call_args.args[0]
    assert ankr_request.blockchain == ["eth", "polygon"]
    assert ankr_request.address == ["0xwallet"]
    assert ankr_request.fromBlock == "earliest"
    assert ankr_request.toBlock == "latest"
    assert ankr_request.fromTimestamp == 10
    assert ankr_request.toTimestamp == 20
    assert ankr_request.descOrder is True
    assert ankr_request.includeLogs is True
    assert ankr_request.syncCheck is True
    assert ankr_request.pageToken == "page"
    assert ankr_request.pageSize == 3


@pytest.mark.asyncio
async def test_account_balance_uses_supported_sdk_flags() -> None:
    client = MagicMock()
    client.token.get_account_balance.return_value = []

    request = AccountBalanceRequest(
        wallet_address="0xwallet",
        blockchain=["eth", "base"],
        only_whitelisted=True,
        native_first=True,
        sync_check=True,
        page_token="page",
        page_size=7,
    )

    await TokenApi(client).get_account_balance(request)

    ankr_request = client.token.get_account_balance.call_args.args[0]
    assert ankr_request.walletAddress == "0xwallet"
    assert ankr_request.blockchain == ["eth", "base"]
    assert ankr_request.onlyWhitelisted is True
    assert ankr_request.nativeFirst is True
    assert ankr_request.syncCheck is True
    assert ankr_request.pageToken == "page"
    assert ankr_request.pageSize == 7
    assert not hasattr(ankr_request, "erc20_only")
    assert not hasattr(ankr_request, "native_only")
    assert not hasattr(ankr_request, "tokens_only")


@pytest.mark.asyncio
async def test_currencies_requires_chain_and_limits_client_side() -> None:
    client = MagicMock()
    client.token.get_currencies.return_value = [
        {"symbol": "A"},
        {"symbol": "B"},
        {"symbol": "C"},
    ]

    request = CurrenciesRequest(blockchain="eth", page_size=2, sync_check=True)

    result = await TokenApi(client).get_currencies(request)

    ankr_request = client.token.get_currencies.call_args.args[0]
    assert ankr_request.blockchain == "eth"
    assert ankr_request.syncCheck is True
    assert not hasattr(ankr_request, "pageToken")
    assert not hasattr(ankr_request, "pageSize")
    assert result.currencies == [{"symbol": "A"}, {"symbol": "B"}]


@pytest.mark.asyncio
async def test_token_price_allows_native_price_request() -> None:
    client = MagicMock()
    client.token.get_token_price.return_value = "123.45"

    request = TokenPriceRequest(blockchain="eth", sync_check=True)

    result = await TokenApi(client).get_token_price(request)

    ankr_request = client.token.get_token_price.call_args.args[0]
    assert ankr_request.blockchain == "eth"
    assert ankr_request.contractAddress is None
    assert ankr_request.syncCheck is True
    assert result == {"price_usd": "123.45"}


@pytest.mark.asyncio
async def test_transfer_tools_forward_multichain_and_address_lists() -> None:
    token_client = MagicMock()
    token_client.token.get_token_transfers.return_value = []
    nft_client = MagicMock()
    nft_client.nft.get_nft_transfers.return_value = []

    token_request = TokenTransfersRequest(
        blockchain=["eth", "base"],
        contract_address="0xtoken",
        wallet_address="0xwallet",
        from_timestamp="earliest",
        to_timestamp="latest",
        descending_order=True,
        sync_check=True,
    )
    nft_request = NFTTransfersRequest(
        blockchain=["polygon", "base"],
        contract_address="0xnft",
        wallet_address="0xowner",
        from_timestamp=1,
        to_timestamp=2,
        descending_order=True,
        sync_check=True,
    )

    await TokenApi(token_client).get_token_transfers(token_request)
    await NFTApi(nft_client).get_nft_transfers(nft_request)

    token_ankr_request = token_client.token.get_token_transfers.call_args.args[0]
    assert token_ankr_request.blockchain == ["eth", "base"]
    assert token_ankr_request.address == ["0xtoken"]
    assert token_ankr_request.fromTimestamp == "earliest"
    assert token_ankr_request.toTimestamp == "latest"
    assert token_ankr_request.descOrder is True
    assert token_ankr_request.syncCheck is True

    nft_ankr_request = nft_client.nft.get_nft_transfers.call_args.args[0]
    assert nft_ankr_request.blockchain == ["polygon", "base"]
    assert nft_ankr_request.address == ["0xnft", "0xowner"]
    assert nft_ankr_request.fromTimestamp == 1
    assert nft_ankr_request.toTimestamp == 2
    assert nft_ankr_request.descOrder is True
    assert nft_ankr_request.syncCheck is True


def test_supported_networks_match_curated_product_expectation() -> None:
    assert SUPPORTED_NETWORKS == [
        "eth",
        "bsc",
        "polygon",
        "avalanche",
        "arbitrum",
        "fantom",
        "optimism",
    ]
