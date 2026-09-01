from __future__ import annotations

import inspect
import os
import random
import time
from typing import Any, Awaitable, Callable

import httpx


def _coerce_sdk_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, 'model_dump'):
        return value.model_dump()  # type: ignore[no-any-return]
    if hasattr(value, 'to_dict'):
        return value.to_dict()  # type: ignore[no-any-return]
    if hasattr(value, '__dict__'):
        return {key: item for key, item in vars(value).items() if not key.startswith('_')}
    return {'data': value}


class PublicSdkTransport:
    """Thin adapter around the official Public Python SDK with small fallback tolerance."""

    def __init__(self, bearer_token: str, account_id_getter: Callable[[], Awaitable[str]]) -> None:
        try:
            from public_api_sdk import AsyncPublicApiClient, ApiKeyAuthConfig, PublicApiClientConfiguration
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError('publicdotcom-py is required for the preferred Public transport layer.') from exc

        self._client = AsyncPublicApiClient(
            ApiKeyAuthConfig(api_secret_key=bearer_token),
            config=PublicApiClientConfiguration(),
        )
        self._account_id_getter = account_id_getter

    async def _ensure_default_account(self) -> str:
        account_id = await self._account_id_getter()
        config = getattr(self._client, 'config', None)
        if config is not None and hasattr(config, 'default_account_number'):
            setattr(config, 'default_account_number', account_id)
        return account_id

    def _resolve_callable(self, candidate_names: list[str]):
        for name in candidate_names:
            if hasattr(self._client, name):
                return getattr(self._client, name)
        raise AttributeError(f'No SDK method matched candidates: {candidate_names}')

    async def _call(self, candidate_names: list[str], *args: Any, **kwargs: Any) -> dict[str, Any]:
        method = self._resolve_callable(candidate_names)
        try:
            result = method(*args, **kwargs)
        except TypeError:
            result = method(*args)
        if inspect.isawaitable(result):
            result = await result
        return _coerce_sdk_payload(result)

    async def get_portfolio(self) -> dict[str, Any]:
        await self._ensure_default_account()
        return await self._call(['get_portfolio'])

    async def get_quotes(self, symbols: list[str], instrument_type: str) -> dict[str, Any]:
        await self._ensure_default_account()
        return await self._call(['get_quotes'], symbols=symbols, instrument_type=instrument_type)

    async def get_option_expirations(self, underlying_symbol: str) -> dict[str, Any]:
        await self._ensure_default_account()
        return await self._call(['get_option_expirations', 'get_options_expirations'], symbol=underlying_symbol)

    async def get_option_chain(self, underlying_symbol: str, expiration: str | None = None) -> dict[str, Any]:
        await self._ensure_default_account()
        kwargs = {'symbol': underlying_symbol}
        if expiration:
            kwargs['expiration'] = expiration
        return await self._call(['get_option_chain', 'get_options_chain'], **kwargs)

    async def place_order(self, order_payload: dict[str, Any]) -> dict[str, Any]:
        await self._ensure_default_account()
        return await self._call(['place_order'], order_payload)

    async def close(self) -> None:
        close_method = getattr(self._client, 'close', None) or getattr(self._client, 'aclose', None)
        if close_method is None:
            return
        result = close_method()
        if inspect.isawaitable(result):
            await result


class PublicApiClient:
    """Self-bootstrapping Public client.

    Authentication flow (per https://public.com/api/docs/quickstart):
      1. The user generates a *secret key* from the Public.com settings page.
      2. The client POSTs the secret key to the token endpoint to obtain a
         short-lived access token.
      3. The access token is used as ``Authorization: Bearer <token>`` for
         all subsequent API requests.
      4. Tokens are cached and automatically refreshed before expiry.
    """

    def __init__(
        self,
        config: dict[str, Any],
        api_secret_key: str | None = None,
        access_token: str | None = None,
        sdk_transport: PublicSdkTransport | Any | None = None,
        bootstrap_http_client: httpx.AsyncClient | Any | None = None,
        sleeper: Any = None,
        jitter_fn: Any = None,
    ) -> None:
        retry = config.get('retry', {})
        self.base_url = str(config.get('base_url', '')).rstrip('/')
        self.timeout_seconds = float(config.get('timeout_seconds', 15))
        self.max_attempts = int(retry.get('max_attempts', 4))
        self.base_delay_seconds = float(retry.get('base_delay_seconds', 0.5))
        self.max_delay_seconds = float(retry.get('max_delay_seconds', 8.0))
        self.jitter_seconds = float(retry.get('jitter_seconds', 0.25))
        self.routes = {
            'portfolio_v2': '/userapigateway/trading/{account_id}/portfolio/v2',
            **dict(config.get('routes', {})),
        }

        auth_config = config.get('auth', {})
        self._token_endpoint = auth_config.get('token_endpoint', '/userapiauthservice/personal/access-tokens')
        self._token_validity_minutes = int(auth_config.get('token_validity_minutes', 480))

        # The secret key is what the user generates from the Public.com UI.
        # We exchange it for a short-lived access token at runtime.
        self._api_secret_key = api_secret_key or os.getenv('PUBLIC_API_SECRET_KEY', '')
        self._access_token = access_token
        self._token_expires_at: float = 0.0

        self._http = bootstrap_http_client or httpx.AsyncClient(timeout=self.timeout_seconds)
        self._sleep = sleeper or time.sleep
        self._jitter = jitter_fn or random.random
        self._account_id: str | None = None
        self._sdk_transport = sdk_transport
        if self._sdk_transport is None:
            try:
                self._sdk_transport = PublicSdkTransport(self._access_token or '', self.fetch_account_id)
            except RuntimeError:
                self._sdk_transport = None

    @property
    def bearer_token(self) -> str:
        """Return the current access token (lazy-resolved)."""
        return self._access_token or ''

    async def _sleep_async(self, seconds: float) -> None:
        result = self._sleep(seconds)
        if inspect.isawaitable(result):
            await result

    async def _request_with_retry(
        self, method: str, url: str, *, params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Shared retry loop for all HTTP requests."""
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = await self._http.request(
                    method=method.upper(), url=url, params=params, json=json_body, headers=headers,
                )
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f'temporary upstream failure: {response.status_code}',
                        request=response.request, response=response,
                    )
                response.raise_for_status()
                return response
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                retriable = isinstance(exc, httpx.RequestError) or (
                    isinstance(exc, httpx.HTTPStatusError)
                    and exc.response is not None
                    and exc.response.status_code >= 500
                )
                if not retriable or attempt >= self.max_attempts:
                    raise
                delay = min(self.max_delay_seconds, self.base_delay_seconds * (2 ** (attempt - 1)))
                delay += self._jitter() * self.jitter_seconds
                await self._sleep_async(delay)
        raise RuntimeError(f'Public API request failed without a terminal response: {last_error}')

    async def fetch_access_token(self, *, force_refresh: bool = False) -> str:
        """Exchange the API secret key for a short-lived access token.

        Follows the flow documented at https://public.com/api/docs/quickstart:
        POST to /userapiauthservice/personal/access-tokens with the secret key.
        """
        if self._access_token and not force_refresh:
            # Refresh 60 seconds before actual expiry to avoid edge cases.
            if time.time() < self._token_expires_at - 60:
                return self._access_token

        if not self._api_secret_key:
            raise RuntimeError(
                'Cannot fetch access token: PUBLIC_API_SECRET_KEY is not set. '
                'Set the env var or pass api_secret_key to PublicApiClient.'
            )

        url = f'{self.base_url}{self._token_endpoint}'
        payload = {
            'validityInMinutes': self._token_validity_minutes,
            'secret': self._api_secret_key,
        }
        response = await self._request_with_retry(
            'POST', url,
            json_body=payload,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
        )
        data = response.json()
        token = data.get('accessToken') if isinstance(data, dict) else None
        if not token:
            raise RuntimeError(f'Public token exchange failed: accessToken missing in response: {data}')
        self._access_token = token
        self._token_expires_at = time.time() + (self._token_validity_minutes * 60)
        return self._access_token

    @property
    def auth_headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self._access_token or ""}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    async def _ensure_token(self) -> str:
        """Ensure we have a valid access token, fetching one if needed."""
        if not self._access_token:
            return await self.fetch_access_token()
        # Auto-refresh if within 60 seconds of expiry.
        if time.time() >= self._token_expires_at - 60:
            return await self.fetch_access_token(force_refresh=True)
        return self._access_token

    async def _raw_request(
        self, method: str, path: str, *, params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self._ensure_token()
        url = f'{self.base_url}/{path.lstrip("/")}'
        response = await self._request_with_retry(
            method=method.upper(), url=url, params=params, json_body=json_body,
            headers=self.auth_headers,
        )
        if not response.text:
            return {}
        payload = response.json()
        return payload if isinstance(payload, dict) else {'data': payload}

    def resolve_route(self, route_key: str, **path_params: Any) -> str:
        return self.routes[route_key].format(**path_params)

    async def fetch_account_id(self) -> str:
        if self._account_id:
            return self._account_id
        payload = await self._raw_request('GET', self.resolve_route('account'))
        accounts = payload.get('accounts')
        if not isinstance(accounts, list) or not accounts:
            raise RuntimeError('Public account bootstrap failed: accounts list is empty or missing from /trading/account response.')
        account_id = accounts[0].get('accountId')
        if not account_id:
            raise RuntimeError('Public account bootstrap failed: accountId missing from the first account in /trading/account response.')
        self._account_id = str(account_id)
        return self._account_id

    async def get_account(self) -> dict[str, Any]:
        return await self._raw_request('GET', self.resolve_route('account'))

    async def get_portfolio(self) -> dict[str, Any]:
        account_id = await self.fetch_account_id()
        if self._sdk_transport is not None:
            try:
                portfolio = await self._sdk_transport.get_portfolio()
                if isinstance(portfolio, dict) and portfolio:
                    return portfolio
            except Exception:
                pass
        return await self._raw_request('GET', self.resolve_route('portfolio_v2', account_id=account_id))

    async def get_quotes(self, symbols: list[str], instrument_type: str = 'EQUITY') -> dict[str, Any]:
        account_id = await self.fetch_account_id()
        if self._sdk_transport is not None:
            try:
                return await self._sdk_transport.get_quotes(symbols, instrument_type)
            except Exception:
                pass
        payload = {'symbols': symbols, 'instrumentType': instrument_type}
        return await self._raw_request('POST', self.resolve_route('quotes', account_id=account_id), json_body=payload)

    async def get_option_expirations(self, underlying_symbol: str) -> dict[str, Any]:
        account_id = await self.fetch_account_id()
        if self._sdk_transport is not None:
            try:
                return await self._sdk_transport.get_option_expirations(underlying_symbol)
            except Exception:
                pass
        return await self._raw_request('GET', self.resolve_route('expirations'), params={'accountId': account_id, 'symbol': underlying_symbol})

    async def get_option_chain(self, underlying_symbol: str, expiration: str | None = None) -> dict[str, Any]:
        account_id = await self.fetch_account_id()
        if self._sdk_transport is not None:
            try:
                return await self._sdk_transport.get_option_chain(underlying_symbol, expiration)
            except Exception:
                pass
        params = {'accountId': account_id, 'symbol': underlying_symbol}
        if expiration:
            params['expiration'] = expiration
        return await self._raw_request('GET', self.resolve_route('chain'), params=params)

    async def place_order(self, order_payload: dict[str, Any]) -> dict[str, Any]:
        account_id = await self.fetch_account_id()
        if self._sdk_transport is not None:
            try:
                return await self._sdk_transport.place_order(order_payload)
            except Exception:
                pass
        return await self._raw_request('POST', self.resolve_route('orders'), params={'accountId': account_id}, json_body=order_payload)

    async def close(self) -> None:
        if self._sdk_transport is not None and hasattr(self._sdk_transport, 'close'):
            await self._sdk_transport.close()
        close_method = getattr(self._http, 'aclose', None) or getattr(self._http, 'close', None)
        if close_method is None:
            return
        result = close_method()
        if inspect.isawaitable(result):
            await result
