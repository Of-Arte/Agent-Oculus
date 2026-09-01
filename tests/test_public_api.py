from __future__ import annotations

import asyncio
import httpx

from core.exceptions import ExecutionDisabledError
from core.public_api.account import PublicAccountService
from core.public_api.client import PublicApiClient
from core.public_api.options import PublicOptionsService
from core.public_api.orders import PublicOrdersService
from conftest import AsyncMockHttpClient, MockResponse, MockSdkTransport

_PORTFOLIO_PAYLOAD = {
    'accountId': 'acct-1',
    'accountType': 'INDIVIDUAL',
    'buyingPower': {
        'buyingPower': '1250.00',
        'cashOnlyBuyingPower': '400.00',
        'optionsBuyingPower': '850.00',
    },
    'equity': [
        {'amount': '2000.00'}
    ],
    'positions': [
        {
            'instrument': {'symbol': 'AAPL', 'name': 'Apple Inc.', 'type': 'EQUITY'},
            'quantity': '2',
            'currentValue': '400.00',
            'lastPrice': {'lastPrice': '200.00'},
            'instrumentGain': {'gainValue': '40.00', 'gainPercentage': '11.11'},
            'costBasis': {'totalCost': '360.00', 'unitCost': '180.00', 'gainValue': '40.00', 'gainPercentage': '11.11'},
        }
    ],
    'orders': [
        {
            'orderId': 'ord-1',
            'instrument': {'symbol': 'AAPL', 'type': 'EQUITY'},
            'type': 'LIMIT',
            'side': 'BUY',
            'status': 'OPEN',
            'quantity': '2',
            'limitPrice': '195.00',
            'filledQuantity': '0',
            'averagePrice': '',
            'createdAt': '2026-01-01T00:00:00Z',
            'closedAt': None,
        }
    ],
}


def _token_response() -> MockResponse:
    """Standard token-exchange response: POST secret -> access token."""
    return MockResponse(200, payload={'accessToken': 'access-token-abc123'})


def _make_client(base_config, bootstrap_http, sdk_transport=None, api_secret_key='secret-key-123'):
    return PublicApiClient(
        base_config['public'],
        api_secret_key=api_secret_key,
        sdk_transport=sdk_transport,
        bootstrap_http_client=bootstrap_http,
        sleeper=lambda _: None,
        jitter_fn=lambda: 0,
    )


def test_public_client_exchanges_secret_key_for_access_token(base_config):
    """The client should POST the secret key to the token endpoint and cache the access token."""
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # token exchange
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-123'}]}),
        ])
        client = _make_client(base_config, bootstrap_http)
        token = await client.fetch_access_token()
        assert token == 'access-token-abc123'
        # Verify the token exchange request
        assert len(bootstrap_http.calls) == 1
        call = bootstrap_http.calls[0]
        assert call['method'] == 'POST'
        assert 'access-tokens' in call['url']
        assert call['json']['secret'] == 'secret-key-123'
        assert 'validityInMinutes' in call['json']
        assert call['headers']['Content-Type'] == 'application/json'
        await client.close()
    asyncio.run(scenario())


def test_public_client_caches_access_token(base_config):
    """After fetching a token, subsequent calls should reuse it without re-exchanging."""
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # only one token exchange expected
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-123'}]}),
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-123'}]}),
        ])
        client = _make_client(base_config, bootstrap_http)
        await client.fetch_access_token()
        await client.fetch_access_token()  # should be cached
        await client.fetch_account_id()
        # Only the token exchange call should have been made; account_id calls use _raw_request
        token_calls = [c for c in bootstrap_http.calls if c['method'] == 'POST' and 'access-tokens' in c['url']]
        assert len(token_calls) == 1
        await client.close()
    asyncio.run(scenario())


def test_public_client_uses_access_token_in_requests(base_config):
    """Subsequent API requests must use the fetched access token as a bearer token."""
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # token exchange
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-123'}]}),
        ])
        client = _make_client(base_config, bootstrap_http)
        await client.fetch_access_token()
        account_id = await client.fetch_account_id()
        assert account_id == 'acct-123'
        # The account request should carry the bearer token
        account_call = [c for c in bootstrap_http.calls if c['method'] == 'GET' and c['url'].endswith('/account')]
        assert len(account_call) == 1
        assert account_call[0]['headers']['Authorization'] == 'Bearer access-token-abc123'
        await client.close()
    asyncio.run(scenario())


def test_public_client_bootstraps_account_id_once(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # token exchange
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-123'}]}),
        ])
        client = _make_client(base_config, bootstrap_http, sdk_transport=MockSdkTransport(portfolio={}))
        assert await client.fetch_account_id() == 'acct-123'
        assert await client.fetch_account_id() == 'acct-123'
        account_calls = [c for c in bootstrap_http.calls if c['method'] == 'GET' and c['url'].endswith('/account')]
        assert len(account_calls) == 1
        await client.close()
    asyncio.run(scenario())


def test_public_client_retries_bootstrap_request(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # token exchange
            httpx.ConnectError('boom'),
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-123'}]}),
        ])
        client = _make_client(base_config, bootstrap_http, sdk_transport=MockSdkTransport(portfolio={}))
        assert await client.fetch_account_id() == 'acct-123'
        account_calls = [c for c in bootstrap_http.calls if c['method'] == 'GET' and c['url'].endswith('/account')]
        assert len(account_calls) == 2
        await client.close()
    asyncio.run(scenario())


def test_get_portfolio_uses_confirmed_url(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # token exchange
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-1'}]}),
            MockResponse(200, payload=_PORTFOLIO_PAYLOAD),
        ])
        client = _make_client(base_config, bootstrap_http, sdk_transport=None)
        payload = await client.get_portfolio()
        assert payload['accountId'] == 'acct-1'
        # Find the portfolio call (should be the 3rd call: token, account, portfolio)
        portfolio_call = bootstrap_http.calls[2]
        assert portfolio_call['url'].endswith('/userapigateway/trading/acct-1/portfolio/v2')
        assert portfolio_call['headers']['Authorization'] == 'Bearer access-token-abc123'
        await client.close()
    asyncio.run(scenario())


def test_account_service_normalizes_portfolio_response(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # token exchange
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-1'}]}),
            MockResponse(200, payload=_PORTFOLIO_PAYLOAD),
            MockResponse(200, payload=_PORTFOLIO_PAYLOAD),
            MockResponse(200, payload=_PORTFOLIO_PAYLOAD),
        ])
        client = _make_client(base_config, bootstrap_http, sdk_transport=None)
        service = PublicAccountService(client)
        snapshot = await service.get_account_snapshot()
        positions = await service.list_positions()
        orders = await service.list_orders()
        assert snapshot.account_id == 'acct-1'
        assert snapshot.buying_power == 1250.0
        assert snapshot.cash == 400.0
        assert snapshot.equity == 2000.0
        assert positions[0].symbol == 'AAPL'
        assert positions[0].quantity == 2.0
        assert positions[0].market_value == 400.0
        assert positions[0].average_cost == 180.0
        assert positions[0].unrealized_pnl == 40.0
        assert orders[0].order_id == 'ord-1'
        assert orders[0].raw['quantity'] == 2.0
        assert orders[0].raw['limitPrice'] == 195.0
        assert orders[0].raw['filledQuantity'] == 0.0
        assert orders[0].raw['averagePrice'] is None
        await client.close()
    asyncio.run(scenario())


def test_place_order_is_gated(base_config, monkeypatch):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # token exchange
            MockResponse(200, payload={'accounts': [{'accountId': 'acct-1'}]}),
        ])
        client = _make_client(base_config, bootstrap_http, sdk_transport=MockSdkTransport())
        service = PublicOrdersService(client, base_config)
        monkeypatch.setenv('EXECUTION_ENABLED', 'false')
        try:
            await service.place_order({'symbol': 'AAPL'})
        except ExecutionDisabledError:
            assert True
        else:
            raise AssertionError('Expected ExecutionDisabledError when execution is disabled')
        await client.close()
    asyncio.run(scenario())


def test_greeks_cast_from_string(base_config):
    service = PublicOptionsService(PublicApiClient(
        base_config['public'],
        sdk_transport=MockSdkTransport(),
        bootstrap_http_client=AsyncMockHttpClient([_token_response()]),
        sleeper=lambda _: None,
        jitter_fn=lambda: 0,
    ))
    contracts = service.normalize_chain('AAPL', {'contracts': [{'symbol': 'AAPL250117C00190000', 'optionType': 'CALL', 'strike': '190', 'bid': '4.10', 'ask': '4.30', 'last': '4.20', 'delta': '0.45', 'gamma': '0.10', 'theta': '-0.05', 'vega': '0.12', 'rho': '0.03', 'iv': '0.22'}]})
    assert contracts[0].delta == 0.45
    assert isinstance(contracts[0].delta, float)
    assert contracts[0].strike == 190.0
    assert contracts[0].iv == 0.22


def test_public_bootstrap_empty_accounts_raises(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # token exchange
            MockResponse(200, payload={'accounts': []}),
        ])
        client = _make_client(base_config, bootstrap_http, sdk_transport=MockSdkTransport(portfolio={}))
        try:
            await client.fetch_account_id()
        except RuntimeError as exc:
            msg = str(exc).lower()
            assert 'bootstrap failed' in msg
            assert 'accounts' in msg
        else:
            raise AssertionError('Expected RuntimeError when accounts list is empty')
        await client.close()
    asyncio.run(scenario())


def test_public_bootstrap_missing_account_id_raises(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([
            _token_response(),  # token exchange
            MockResponse(200, payload={'accounts': [{'accountId': ''}]}),
        ])
        client = _make_client(base_config, bootstrap_http, sdk_transport=MockSdkTransport(portfolio={}))
        try:
            await client.fetch_account_id()
        except RuntimeError as exc:
            msg = str(exc).lower()
            assert 'bootstrap failed' in msg
            assert 'accountid' in msg
        else:
            raise AssertionError('Expected RuntimeError when accountId is missing')
        await client.close()
    asyncio.run(scenario())


def test_fetch_access_token_without_secret_raises(base_config):
    async def scenario() -> None:
        bootstrap_http = AsyncMockHttpClient([])
        client = PublicApiClient(
            base_config['public'],
            api_secret_key=None,
            bootstrap_http_client=bootstrap_http,
            sleeper=lambda _: None,
            jitter_fn=lambda: 0,
        )
        try:
            await client.fetch_access_token()
        except RuntimeError as exc:
            assert 'PUBLIC_API_SECRET_KEY' in str(exc)
        else:
            raise AssertionError('Expected RuntimeError when secret key is missing')
        await client.close()
    asyncio.run(scenario())
