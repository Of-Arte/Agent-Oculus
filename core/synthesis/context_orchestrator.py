"""Context orchestration — the glue between service clients and FinanceContext.

This module lives in core/synthesis/ and serves as the single entry point for
building a FinanceContext. It contains the orchestration logic that was
previously in the standalone tools/get_signals.py CLI entry point,
consolidated here so the plugin layer (plugins/oculus/tools.py) imports
directly from core/.

The config resolution and healthcheck version utilities were moved to
core/_version.py (Phase 3); this module focuses purely on orchestration.
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
from core.synthesis.context_builder import build_finance_context
from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.client import WorldMonitorClient
from core.worldmonitor.macro import WorldMonitorMacroService
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from core.worldmonitor.trade_policy import WorldMonitorTradePolicyService


# ---------------------------------------------------------------------------
# Noop fallbacks — used when broker/WM credentials are absent so the pipeline
# degrades gracefully (macro + IV analysis still work).
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


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------

def find_config_path(config_path: str | Path | None = None) -> Path:
    """Resolve config.yaml relative to the profile root, not cwd.

    When the plugin runs from ~/.hermes/plugins/oculus/, the cwd is not
    the profile root, so a relative 'config.yaml' would fail.

    Resolution order:
      1. Explicit config_path if provided and exists
      2. REPO_ROOT env var (dev/test override)
      3. Profile root via core._version.get_profile_root()
      4. cwd (fallback)
    """
    if config_path is not None:
        p = Path(config_path)
        if p.is_absolute() or p.exists():
            return p

    # Try REPO_ROOT
    repo_root = os.environ.get("REPO_ROOT")
    if repo_root:
        candidate = Path(repo_root) / "config.yaml"
        if candidate.exists():
            return candidate

    # Try profile root from core._version
    try:
        candidate = get_profile_root() / "config.yaml"
        if candidate.exists():
            return candidate
    except Exception:
        pass

    # Fallback: cwd
    return Path.cwd() / "config.yaml"


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load config.yaml, resolving the path relative to the profile root."""
    resolved = find_config_path(config_path)
    with resolved.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def build_context(config_path: str | Path | None = None):
    """Build the full FinanceContext with all service clients.

    Instantiates Public.com and WorldMonitor clients (or noops when
    credentials are absent), calls build_finance_context(), and ensures
    clients are closed on exit.

    Args:
        config_path: Optional explicit path to config.yaml. If None,
            resolves relative to the profile root.
    """
    config = load_config(config_path)
    public_enabled = bool(os.environ.get('PUBLIC_API_SECRET_KEY'))
    wm_enabled = bool(os.environ.get('WM_BASE_URL'))

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
        return context
    finally:
        if public_client is not None:
            await public_client.close()
        if wm_client is not None:
            await wm_client.close()


async def get_signals_dict(symbols: list[str] | None = None, config_path: str | Path | None = None) -> dict:
    """Full finance context synthesis — regime, regime_flags, signals, alerts.

    Optionally filter to specific symbols.
    Delegates to build_finance_context() which orchestrates Public.com
    and WorldMonitor service clients.

    Args:
        symbols: Optional list of tickers to filter signals/alerts to.
        config_path: Optional explicit path to config.yaml.
    """
    context = await build_context(config_path)
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


def run(symbols: list[str] | None = None, config_path: str | Path | None = None) -> dict:
    """Synchronous entrypoint — full finance context synthesis.

    Called by plugins/oculus/tools.py:oculus_get_context().
    """
    return asyncio.run(get_signals_dict(symbols, config_path))
