"""Orchestrator Adapter — thin wiring that builds bundles and calls the deep Module.

This module lives at the Hermes/CLI Seam. It resolves config, creates
( or noops ) service Adapters, bundles them, and delegates to
core.synthesis.context.build_finance_context. No fetch logic lives here.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, cast

import yaml

from core._version import get_profile_root
from core.public_api.account import PublicAccountService
from core.public_api.client import PublicApiClient
from core.public_api.market_data import PublicMarketDataService
from core.public_api.options import PublicOptionsService
from core.synthesis.context import PublicBundle, WorldMonitorBundle, build_finance_context
from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.client import WorldMonitorClient
from core.worldmonitor.macro import WorldMonitorMacroService
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from core.worldmonitor.trade_policy import WorldMonitorTradePolicyService

# ---------------------------------------------------------------------------
# Noop fallbacks — degrade gracefully when creds absent
# ---------------------------------------------------------------------------


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
            return {"contracts": [], "iv_rank": None}

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


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------


def find_config_path(config_path: str | Path | None = None) -> Path:
    if config_path is not None:
        p = Path(config_path)
        if p.is_absolute() or p.exists():
            return p
    repo_root = os.environ.get("REPO_ROOT")
    if repo_root:
        candidate = Path(repo_root) / "config.yaml"
        if candidate.exists():
            return candidate
    try:
        candidate = get_profile_root() / "config.yaml"
        if candidate.exists():
            return candidate
    except Exception:
        pass
    return Path.cwd() / "config.yaml"


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    resolved = find_config_path(config_path)
    with resolved.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


# ---------------------------------------------------------------------------
# Bundle factories
# ---------------------------------------------------------------------------


def _build_public_bundle(public_client: PublicApiClient | None) -> PublicBundle:
    if public_client is None:
        return PublicBundle(
            account=cast(PublicAccountService, _NoopPublicAccountService()),
            market_data=cast(PublicMarketDataService, _NoopPublicMarketDataService()),
            options=cast(PublicOptionsService, _NoopPublicOptionsService()),
        )
    return PublicBundle(
        account=cast(PublicAccountService, PublicAccountService(public_client)),
        market_data=cast(PublicMarketDataService, PublicMarketDataService(public_client)),
        options=cast(PublicOptionsService, PublicOptionsService(public_client)),
    )


def _build_wm_bundle(wm_client: WorldMonitorClient | None) -> WorldMonitorBundle:
    if wm_client is None:
        noop = _NoopWorldMonitorService()
        return WorldMonitorBundle(
            macro=cast(WorldMonitorMacroService, noop),
            market_radar=cast(WorldMonitorMarketRadarService, noop),
            stablecoin=cast(WorldMonitorStablecoinService, noop),
            etf_flow=cast(WorldMonitorBtcEtfFlowService, noop),
            supply_chain=cast(WorldMonitorSupplyChainService, noop),
            trade_policy=cast(WorldMonitorTradePolicyService, noop),
        )
    return WorldMonitorBundle(
        macro=cast(WorldMonitorMacroService, WorldMonitorMacroService(wm_client)),
        market_radar=cast(WorldMonitorMarketRadarService, WorldMonitorMarketRadarService(wm_client)),
        stablecoin=cast(WorldMonitorStablecoinService, WorldMonitorStablecoinService(wm_client)),
        etf_flow=cast(WorldMonitorBtcEtfFlowService, WorldMonitorBtcEtfFlowService(wm_client)),
        supply_chain=cast(WorldMonitorSupplyChainService, WorldMonitorSupplyChainService(wm_client)),
        trade_policy=cast(WorldMonitorTradePolicyService, WorldMonitorTradePolicyService(wm_client)),
    )


# ---------------------------------------------------------------------------
# Orchestration — thin Adapter
# ---------------------------------------------------------------------------


async def build_context(config_path: str | Path | None = None):
    config = load_config(config_path)
    public_enabled = bool(os.environ.get("PUBLIC_API_SECRET_KEY"))
    wm_enabled = bool(os.environ.get("WM_BASE_URL"))
    public_client = PublicApiClient(config.get("public", {})) if public_enabled else None
    wm_client = WorldMonitorClient() if wm_enabled else None
    try:
        public_bundle = _build_public_bundle(public_client)
        wm_bundle = _build_wm_bundle(wm_client)
        return await build_finance_context(public=public_bundle, wm=wm_bundle)
    finally:
        if public_client is not None:
            await public_client.close()
        if wm_client is not None:
            await wm_client.close()


async def get_signals_dict(symbols: list[str] | None = None, config_path: str | Path | None = None) -> dict:
    context = await build_context(config_path)
    signals = context.signals
    alerts = context.alerts
    if symbols:
        symbol_set = {s.upper() for s in symbols}
        signals = [sig for sig in signals if sig.symbol is None or sig.symbol.upper() in symbol_set]
        alerts = [a for a in alerts if a.ticker is None or a.ticker.upper() in symbol_set]
    return {
        "regime": context.regime,
        "regime_flags": context.regime_flags,
        "signals": [s.to_dict() for s in signals],
        "alerts": [a.to_dict() for a in alerts],
    }


def run(symbols: list[str] | None = None, config_path: str | Path | None = None) -> dict:
    return asyncio.run(get_signals_dict(symbols, config_path))
