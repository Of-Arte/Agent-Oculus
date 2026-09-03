"""Shim: preserves 9-param Interface for backwards compatibility.

Canonical Module is now core.synthesis.context (2-bundle Interface).
This file delegates to it so existing imports keep working.
"""
from __future__ import annotations

import warnings
from typing import Any

from core.public_api.account import PublicAccountService
from core.public_api.market_data import PublicMarketDataService
from core.public_api.options import PublicOptionsService
from core.synthesis.context import PublicBundle, WorldMonitorBundle, build_finance_context as _bundled_build
from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.macro import WorldMonitorMacroService
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from core.worldmonitor.trade_policy import WorldMonitorTradePolicyService

# Re-export bundles and helpers for callers that import from here
__all__ = ["build_finance_context", "PublicBundle", "WorldMonitorBundle"]

# Re-export internal helpers expected by some callers (used via import)
from core.synthesis.context import _estimate_atm_iv, _yfinance_atm_iv  # noqa: F401


async def build_finance_context(
    *,
    public_account_service: PublicAccountService,
    public_market_data_service: PublicMarketDataService,
    public_options_service: PublicOptionsService,
    wm_market_radar_service: WorldMonitorMarketRadarService,
    wm_stablecoin_service: WorldMonitorStablecoinService,
    wm_etf_flow_service: WorldMonitorBtcEtfFlowService,
    wm_macro_service: WorldMonitorMacroService,
    wm_supply_chain_service: WorldMonitorSupplyChainService,
    wm_trade_policy_service: WorldMonitorTradePolicyService,
    previous_regime: str | None = None,
    include: set[str] | None = None,
) -> Any:
    warnings.warn(
        "9-param build_finance_context is deprecated; use context.PublicBundle + WorldMonitorBundle",
        DeprecationWarning,
        stacklevel=2,
    )
    public = PublicBundle(
        account=public_account_service,
        market_data=public_market_data_service,
        options=public_options_service,
    )
    wm = WorldMonitorBundle(
        macro=wm_macro_service,
        market_radar=wm_market_radar_service,
        stablecoin=wm_stablecoin_service,
        etf_flow=wm_etf_flow_service,
        supply_chain=wm_supply_chain_service,
        trade_policy=wm_trade_policy_service,
    )
    return await _bundled_build(public=public, wm=wm, previous_regime=previous_regime, include=include)
