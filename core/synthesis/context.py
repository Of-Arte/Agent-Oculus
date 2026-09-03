"""Canonical deep Module for finance context synthesis.

This is the single deep Module behind a small Interface (2 bundles).
It consolidates the orchestration previously split across context_builder.py
and context_orchestrator.py. Those files remain as thin shims re-exporting
from here for backwards compatibility.

Interface (external Seam):
    build_finance_context(*, public: PublicBundle, wm: WorldMonitorBundle,
                         symbols=None, include=None, previous_regime=None) -> FinanceContext

Bundles are the adapters at the Seam — two names to learn instead of nine.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass
from typing import Any

from core.analytics.iv_rank import IVRankEngine
from core.public_api.account import PublicAccountService
from core.public_api.market_data import PublicMarketDataService
from core.public_api.options import PublicOptionsService
from core.schemas import FinanceContext, MarketRadarVerdict, FearGreedIndex, Quote, PortfolioSnapshot, utc_now_iso
from core.synthesis.alert_engine import build_normalized_signals, evaluate_alerts
from core.synthesis.regime_detector import detect_regime
from core.worldmonitor.btc_etf_flows import WorldMonitorBtcEtfFlowService
from core.worldmonitor.client import WMError, WorldMonitorClient
from core.worldmonitor.macro import WorldMonitorMacroService
from core.worldmonitor.market_radar import WorldMonitorMarketRadarService
from core.worldmonitor.stablecoins import WorldMonitorStablecoinService
from core.worldmonitor.supply_chain import WorldMonitorSupplyChainService
from core.worldmonitor.trade_policy import WorldMonitorTradePolicyService

logger = logging.getLogger(__name__)

_IV_ENGINE = IVRankEngine(lookback_days=252)

# ---------------------------------------------------------------------------
# Bundles — the small Interface (2 params instead of 9)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class PublicBundle:
    """Broker-side adapters."""

    account: Any  # PublicAccountService (Any to allow stub adapters in tests)
    market_data: Any  # PublicMarketDataService
    options: Any  # PublicOptionsService


@dataclass(slots=True)
class WorldMonitorBundle:
    """WorldMonitor-side adapters."""

    macro: Any  # WorldMonitorMacroService
    market_radar: Any  # WorldMonitorMarketRadarService
    stablecoin: Any  # WorldMonitorStablecoinService
    etf_flow: Any  # WorldMonitorBtcEtfFlowService
    supply_chain: Any  # WorldMonitorSupplyChainService
    trade_policy: Any  # WorldMonitorTradePolicyService


# ---------------------------------------------------------------------------
# Internal helpers (not part of Interface)
# ---------------------------------------------------------------------------


def _parse_dte(expiration: str | None) -> int:
    if not expiration:
        return 0
    try:
        from datetime import date

        y, m, d = expiration.split("-")
        exp = date(int(y), int(m), int(d))
        today = date.today()
        return max(0, (exp - today).days)
    except Exception:
        return 0


def _estimate_atm_iv(*, quote: Quote | None, chain) -> float | None:
    underlying = None
    if quote is not None:
        underlying = quote.price
    contracts = getattr(chain, "contracts", None) or []
    if underlying is not None and contracts:
        best = None
        best_dist = None
        for c in contracts:
            if c.strike is None or c.iv is None:
                continue
            dist = abs(float(c.strike) - float(underlying))
            if best_dist is None or dist < best_dist:
                best = c
                best_dist = dist
        if best is not None and best.iv is not None:
            return float(best.iv)
    iv_metrics = getattr(chain, "iv_metrics", None)
    if iv_metrics is not None and getattr(iv_metrics, "implied_volatility", None) is not None:
        return float(iv_metrics.implied_volatility)
    return None


async def _yfinance_atm_iv(symbol: str, quote: Quote | None) -> float | None:
    loop = asyncio.get_running_loop()

    def _fetch() -> float | None:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        expirations = list(getattr(ticker, "options", []) or [])
        if not expirations:
            return None
        exp = expirations[0]
        underlying = None
        if quote is not None:
            underlying = quote.price
        if underlying is None:
            hist = ticker.history(period="5d", interval="1d")
            if hasattr(hist, "empty") and not hist.empty and "Close" in hist.columns:
                underlying = float(hist["Close"].dropna().iloc[-1])
        chain = ticker.option_chain(exp)
        calls = getattr(chain, "calls", None)
        puts = getattr(chain, "puts", None)
        frames = [df for df in [calls, puts] if df is not None]
        if not frames:
            return None
        best_iv = None
        best_dist = None
        for df in frames:
            if "strike" not in df.columns or "impliedVolatility" not in df.columns:
                continue
            for _, row in df.iterrows():
                strike = row.get("strike")
                iv = row.get("impliedVolatility")
                if strike is None or iv is None:
                    continue
                if underlying is None:
                    continue
                dist = abs(float(strike) - float(underlying))
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_iv = float(iv)
        return best_iv

    return await loop.run_in_executor(None, _fetch)


async def _noop_list() -> list:
    return []


async def _guard(coro, label: str):
    try:
        return await coro
    except WMError as exc:
        logger.warning("WorldMonitor fetch failed for %s: %s", label, exc)
        print(f"[WM WARNING] {label} failed: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Deep Module — single entry point
# ---------------------------------------------------------------------------

# Valid include keys for selective fetching (agentic slice queries)
_VALID_INCLUDE = {
    "macro",
    "radar",
    "fear_greed",
    "stablecoin",
    "etf",
    "energy",
    "chokepoint",
    "trade",
    "bis",
}


async def build_finance_context(
    *,
    public: PublicBundle,
    wm: WorldMonitorBundle,
    previous_regime: str | None = None,
    include: set[str] | None = None,
) -> FinanceContext:
    """Aggregates and builds a comprehensive FinanceContext.

    Deep Implementation: concurrent broker + WM fetches, IV rank via
    yfinance fallback, regime detection, signal normalization, alert eval.

    Args:
        public: Broker adapters bundle.
        wm: WorldMonitor adapters bundle.
        previous_regime: Previously detected regime for state tracking.
        include: Optional subset of WM slices to fetch. Valid keys:
            macro, radar, fear_greed, stablecoin, etf, energy,
            chokepoint, trade, bis. None = all.
    """
    if include is not None:
        unknown = include - _VALID_INCLUDE
        if unknown:
            raise ValueError(f"Unknown include keys: {unknown}. Valid: {_VALID_INCLUDE}")

    def _wanted(key: str) -> bool:
        return include is None or key in include

    # Broker fetches
    account = None
    positions: list = []
    try:
        account = await public.account.get_account_snapshot()
        positions = await public.account.list_positions()
    except Exception as exc:
        logger.warning("Public account fetch failed (continuing read-only): %s", exc)

    active_symbols = [p.symbol for p in positions if p.quantity]
    analysis_symbols = active_symbols or ["SPY", "QQQ", "XLE"]

    quotes: dict = {}
    if analysis_symbols:
        try:
            quotes = await public.market_data.get_quotes(analysis_symbols)
        except Exception as exc:
            logger.warning("Quote fetch failed (continuing): %s", exc)
            quotes = {}

    # Concurrent I/O: options chains + WM slices
    options_tasks = [
        asyncio.create_task(public.options.get_normalized_chain(symbol)) for symbol in analysis_symbols
    ]

    # Build WM gather list conditionally
    wm_labels: list[str] = []
    wm_coros: list[Any] = []
    if _wanted("macro"):
        wm_labels.append("macro")
        wm_coros.append(_guard(wm.macro.get_macro_signals(), "macro"))
    if _wanted("radar"):
        wm_labels.append("market_radar")
        wm_coros.append(_guard(wm.market_radar.get_market_radar_verdict(), "market_radar"))
    if _wanted("fear_greed"):
        wm_labels.append("fear_greed")
        wm_coros.append(_guard(wm.market_radar.get_fear_greed(), "fear_greed"))
    if _wanted("stablecoin"):
        wm_labels.append("stablecoins")
        wm_coros.append(_guard(wm.stablecoin.list_stablecoin_markets(), "stablecoins"))
    if _wanted("etf"):
        wm_labels.append("etf_flows")
        wm_coros.append(_guard(wm.etf_flow.list_etf_flows(), "etf_flows"))
    if _wanted("energy"):
        wm_labels.append("energy")
        wm_coros.append(_guard(wm.macro.get_energy_prices(), "energy"))
    if _wanted("chokepoint"):
        wm_labels.append("chokepoints")
        wm_coros.append(_guard(wm.supply_chain.get_chokepoint_status(), "chokepoints"))
    if _wanted("trade"):
        wm_labels.append("trade_restrictions")
        wm_coros.append(_guard(wm.trade_policy.get_trade_restrictions(), "trade_restrictions"))
    if _wanted("bis"):
        wm_labels.append("bis_policy_rates")
        wm_coros.append(_guard(wm.macro.get_bis_policy_rates(), "bis_policy_rates"))

    async def _gather_wm():
        if not wm_coros:
            return []
        return await asyncio.gather(*wm_coros)

    options_results, wm_results = await asyncio.gather(
        asyncio.gather(*options_tasks, return_exceptions=True) if options_tasks else _noop_list(),
        _gather_wm(),
    )

    # Map wm_results back to named slots (None for excluded slices)
    wm_map: dict[str, Any] = {label: None for label in _VALID_INCLUDE}
    # Also map the gather labels
    for label, value in zip(wm_labels, wm_results):
        if label == "market_radar":
            wm_map["radar"] = value
        elif label == "stablecoins":
            wm_map["stablecoin"] = value
        elif label == "etf_flows":
            wm_map["etf"] = value
        elif label == "chokepoints":
            wm_map["chokepoint"] = value
        elif label == "trade_restrictions":
            wm_map["trade"] = value
        elif label == "bis_policy_rates":
            wm_map["bis"] = value
        else:
            wm_map[label] = value

    macro = wm_map.get("macro")
    market_radar = wm_map.get("radar")
    fear_greed = wm_map.get("fear_greed")
    stablecoins = wm_map.get("stablecoin")
    etf_flows = wm_map.get("etf")
    energy = wm_map.get("energy")
    chokepoints = wm_map.get("chokepoint")
    trade_restrictions = wm_map.get("trade")
    bis_policy_rates = wm_map.get("bis")

    # Normalize wm slices that may be [] vs None for downstream
    # (keep None distinction for regime detector defaults)

    options_chains: dict = {}
    for symbol, result in zip(analysis_symbols, options_results):
        if isinstance(result, Exception):
            logger.warning("Options chain fetch failed for %s: %s", symbol, result)
        else:
            options_chains[symbol] = result

    # IV rank analysis
    iv_rank_tasks: list[Any] = []
    for symbol in analysis_symbols:
        chain = options_chains.get(symbol)
        quote = quotes.get(symbol)
        current_iv = _estimate_atm_iv(quote=quote, chain=chain) if chain is not None else None
        if current_iv is None:
            try:
                current_iv = await _yfinance_atm_iv(symbol, quote)
            except Exception as exc:
                logger.warning("yfinance ATM IV fetch failed for %s: %s", symbol, exc)
                current_iv = None
        if current_iv is None:
            continue
        iv_rank_tasks.append(asyncio.create_task(_IV_ENGINE.compute(symbol, float(current_iv))))

    iv_ranks: list = []
    if iv_rank_tasks:
        for item in await asyncio.gather(*iv_rank_tasks, return_exceptions=True):
            if isinstance(item, Exception):
                logger.warning("IV rank compute failed: %s", item)
                continue
            iv_ranks.append(item)

    default_verdict = MarketRadarVerdict(verdict="CASH", bullish_count=0, total_known=0, signals={}, mayer_multiple=None, timestamp=utc_now_iso())
    default_fg = FearGreedIndex(value=50, classification="UNKNOWN", timestamp=utc_now_iso())
    default_chokepoints = chokepoints or []
    default_stablecoins = stablecoins or []

    regime_result = detect_regime(market_radar or default_verdict, fear_greed or default_fg, default_chokepoints, default_stablecoins)

    # Build canonical Portfolio View alongside legacy account+positions
    portfolio = None
    if account is not None:
        portfolio = PortfolioSnapshot(
            account_id=account.account_id,
            generated_at=utc_now_iso(),
            buying_power=account.buying_power,
            cash=account.cash,
            equity=account.equity,
            positions=list(positions),
            raw=dict(account.raw),
        )

    context = FinanceContext(
        account=account,
        positions=positions,
        quotes=quotes,
        options_chains=options_chains,
        macro=macro,
        market_radar=market_radar,
        fear_greed=fear_greed,
        stablecoins=stablecoins,
        etf_flows=etf_flows,
        energy=energy,
        chokepoints=chokepoints,
        trade_restrictions=trade_restrictions,
        bis_policy_rates=bis_policy_rates,
        iv_ranks=iv_ranks,
        signals=[],
        regime=regime_result.regime,
        regime_flags=regime_result.flags,
        timestamp=utc_now_iso(),
        previous_regime=previous_regime,
        portfolio=portfolio,
    )
    context.signals = build_normalized_signals(context)
    context.alerts = evaluate_alerts(context)
    return context
