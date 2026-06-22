from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

PROFILE_HOME = Path(__file__).resolve().parents[2]
if str(PROFILE_HOME) not in sys.path:
    sys.path.insert(0, str(PROFILE_HOME))

from core.output.formatter import format_for_hermes
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


def _load_profile_config() -> dict:
    config_path = PROFILE_HOME / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def oculus_healthcheck(args: dict, **kwargs) -> str:
    plugins_dir = PROFILE_HOME / "plugins"
    skills_dir = PROFILE_HOME / "skills"
    skins_dir = PROFILE_HOME / "skins"
    soul_path = PROFILE_HOME / "SOUL.md"
    config_path = PROFILE_HOME / "config.yaml"
    return json.dumps(
        {
            "ok": True,
            "profile_home": str(PROFILE_HOME),
            "assets": {
                "SOUL.md": soul_path.exists(),
                "config.yaml": config_path.exists(),
                "plugins_dir": plugins_dir.is_dir(),
                "skills_dir": skills_dir.is_dir(),
                "skins_dir": skins_dir.is_dir(),
            },
            "env": {
                "PUBLIC_ACCESS_TOKEN": bool(os.environ.get("PUBLIC_ACCESS_TOKEN")),
                "WM_BASE_URL": os.environ.get("WM_BASE_URL", ""),
                "EXECUTION_ENABLED": os.environ.get("EXECUTION_ENABLED", "false"),
            },
            "notes": [
                "Uses Hermes-native profile layout; no OCULUS_WORKDIR shim.",
                "Tools are loaded from the profile distribution and must be explicitly enabled.",
            ],
        },
        indent=2,
    )


def oculus_get_context(args: dict, **kwargs) -> str:
    symbols = args.get("symbols")

    async def _gather():
        out: dict[str, Any] = {"portfolio_snapshot": None, "macro_context": None, "signals": None}
        profile_config = _load_profile_config()

        if os.environ.get("PUBLIC_ACCESS_TOKEN"):
            public_client = PublicApiClient(profile_config.get("public", {}))
            wm_client = WorldMonitorClient()
            try:
                context = await build_finance_context(
                    public_account_service=PublicAccountService(public_client),
                    public_market_data_service=PublicMarketDataService(public_client),
                    public_options_service=PublicOptionsService(public_client),
                    wm_market_radar_service=WorldMonitorMarketRadarService(wm_client),
                    wm_stablecoin_service=WorldMonitorStablecoinService(wm_client),
                    wm_etf_flow_service=WorldMonitorBtcEtfFlowService(wm_client),
                    wm_macro_service=WorldMonitorMacroService(wm_client),
                    wm_supply_chain_service=WorldMonitorSupplyChainService(wm_client),
                    wm_trade_policy_service=WorldMonitorTradePolicyService(wm_client),
                )
                out["signals"] = format_for_hermes(context)
                out["portfolio_snapshot"] = {
                    "account": context.account.to_dict() if context.account else None,
                    "positions": [item.to_dict() for item in context.positions],
                    "signals": [signal.to_dict() for signal in context.signals],
                    "alerts": [alert.to_dict() for alert in context.alerts],
                }
                out["macro_context"] = {
                    "regime": context.regime,
                    "regime_flags": context.regime_flags,
                    "fear_greed": context.fear_greed.to_dict() if context.fear_greed else None,
                    "market_radar": context.market_radar.to_dict() if context.market_radar else None,
                }
            finally:
                await public_client.close()
                await wm_client.close()

        return out

    try:
        result = asyncio.run(_gather())
        return json.dumps({"ok": True, "result": result, "symbols": symbols}, default=str)
    except Exception as e:
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
