from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, cast

import yaml

from core.public_api.account import PublicAccountService
from core.public_api.client import PublicApiClient
from core.public_api.market_data import PublicMarketDataService
from core.public_api.options import PublicOptionsService
from core.synthesis.context_builder import build_finance_context
from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.client import WorldMonitorClient
from core.worldmonitor.macro import WorldMonitorMacroService
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from core.worldmonitor.trade_policy import WorldMonitorTradePolicyService


class _NoopPublicAccountService:
    async def get_account_snapshot(self):
        return None

    async def list_positions(self):
        return []


class _NoopPublicMarketDataService:
    async def get_quotes(self, symbols):
        return {}


class _NoopPublicOptionsService:
    class _NoopOptionChain:
        contracts: list = []
        iv_metrics = None
        expiration = None
        iv_rank = None

        def to_dict(self):
            return {'contracts': [], 'iv_rank': None}

    async def get_normalized_chain(self, symbol, expiration=None):
        return self._NoopOptionChain()


class _NoopWorldMonitorService:
    async def get_macro_signals(self):
        return None

    async def get_market_radar_verdict(self):
        return None

    async def get_fear_greed(self):
        return None

    async def list_stablecoin_markets(self):
        return []

    async def list_etf_flows(self):
        return []

    async def get_energy_prices(self):
        return None

    async def get_chokepoint_status(self):
        return []

    async def get_trade_restrictions(self):
        return []

    async def get_bis_policy_rates(self):
        return []


def load_config(config_path: str | Path = 'config.yaml') -> dict[str, Any]:
    with Path(config_path).open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle) or {}


async def get_signals(symbols: list[str] | None = None, config_path: str | Path = 'config.yaml') -> dict:
    config = load_config(config_path)
    public_enabled = bool(os.getenv('PUBLIC_ACCESS_TOKEN'))
    wm_enabled = bool(os.getenv('WM_BASE_URL'))

    public_client = PublicApiClient(config.get('public', {})) if public_enabled else None
    wm_client = WorldMonitorClient() if wm_enabled else None

    try:
        context = await build_finance_context(
            public_account_service=cast(PublicAccountService, PublicAccountService(public_client)) if public_client else cast(PublicAccountService, _NoopPublicAccountService()),
            public_market_data_service=cast(PublicMarketDataService, PublicMarketDataService(public_client)) if public_client else cast(PublicMarketDataService, _NoopPublicMarketDataService()),
            public_options_service=cast(PublicOptionsService, PublicOptionsService(public_client)) if public_client else cast(PublicOptionsService, _NoopPublicOptionsService()),
            wm_market_radar_service=cast(WorldMonitorMarketRadarService, WorldMonitorMarketRadarService(wm_client)) if wm_client else cast(WorldMonitorMarketRadarService, _NoopWorldMonitorService()),
            wm_stablecoin_service=cast(WorldMonitorStablecoinService, WorldMonitorStablecoinService(wm_client)) if wm_client else cast(WorldMonitorStablecoinService, _NoopWorldMonitorService()),
            wm_etf_flow_service=cast(WorldMonitorBtcEtfFlowService, WorldMonitorBtcEtfFlowService(wm_client)) if wm_client else cast(WorldMonitorBtcEtfFlowService, _NoopWorldMonitorService()),
            wm_macro_service=cast(WorldMonitorMacroService, WorldMonitorMacroService(wm_client)) if wm_client else cast(WorldMonitorMacroService, _NoopWorldMonitorService()),
            wm_supply_chain_service=cast(WorldMonitorSupplyChainService, WorldMonitorSupplyChainService(wm_client)) if wm_client else cast(WorldMonitorSupplyChainService, _NoopWorldMonitorService()),
            wm_trade_policy_service=cast(WorldMonitorTradePolicyService, WorldMonitorTradePolicyService(wm_client)) if wm_client else cast(WorldMonitorTradePolicyService, _NoopWorldMonitorService()),
        )
        signals = context.signals
        alerts = context.alerts
        if symbols:
            symbol_set = {symbol.upper() for symbol in symbols}
            signals = [signal for signal in signals if signal.symbol is None or signal.symbol.upper() in symbol_set]
            alerts = [alert for alert in alerts if alert.ticker is None or alert.ticker.upper() in symbol_set]
        return {
            'regime': context.regime,
            'regime_flags': context.regime_flags,
            'signals': [signal.to_dict() for signal in signals],
            'alerts': [alert.to_dict() for alert in alerts],
        }
    finally:
        if public_client is not None:
            await public_client.close()
        if wm_client is not None:
            await wm_client.close()


def run(symbols: list[str] | None = None, config_path: str | Path = 'config.yaml') -> dict:
    return asyncio.run(get_signals(symbols, config_path))
