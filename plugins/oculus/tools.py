"""Tool handler functions for the oculus plugin.

Handlers use lazy imports of core/ so that schema discovery works before
sys.path is bootstrapped in __init__.py.
"""

from __future__ import annotations

import json
import os
from typing import Any


def oculus_get_context(args: dict, **kwargs) -> str:
    """Run the full finance context synthesis pipeline.

    Delegates to tools.get_signals.run() which asynchronously fetches:
      - Public.com portfolio snapshot, positions, quotes, options chains
      - WorldMonitor macro signals, market radar verdict, fear/greed,
        stablecoins, ETF flows, energy, chokepoints, trade policy, BIS rates

    Returns a JSON string with the formatted context payload.
    Degrades gracefully: if Public.com or WorldMonitor are unavailable,
    returns partial results with clear status markers.
    """
    # Lazy imports — only loaded when this tool is actually called
    from tools.get_signals import run as _get_signals_run

    symbols = args.get("symbols")
    if symbols is not None and isinstance(symbols, list):
        symbols = [str(s) for s in symbols]
    else:
        symbols = None

    try:
        result = _get_signals_run(symbols=symbols)
        return json.dumps(result, indent=2, default=str)
    except Exception as exc:
        return json.dumps(
            {
                "ok": False,
                "error": {
                    "type": "context_build_failed",
                    "message": f"Failed to build finance context: {type(exc).__name__}: {exc}",
                },
            },
            indent=2,
            default=str,
        )


def oculus_healthcheck(args: dict, **kwargs) -> str:
    """Validate environment configuration and service availability.

    Checks:
      - WM_BASE_URL is set and reachable
      - PUBLIC_API_SECRET_KEY is set (or read-only fallback is available)
      - Optional fallback providers (FINNHUB_API_KEY, EIA_API_KEY)
    """
    # Lazy import
    from core.output.formatter import format_for_hermes  # noqa: F401 — verify import works

    import urllib.request
    import urllib.error

    checks: list[dict[str, Any]] = []

    # 1. WM_BASE_URL
    wm_base = os.environ.get("WM_BASE_URL", "").strip()
    if not wm_base:
        checks.append(
            {
                "name": "WM_BASE_URL",
                "status": "missing",
                "message": "Set WM_BASE_URL to your WorldMonitor instance URL.",
            }
        )
    else:
        try:
            url = wm_base.rstrip("/") + "/api/economic/v1/get-macro-signals"
            req = urllib.request.Request(url, method="GET")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.getcode()
            if 200 <= status_code < 300:
                checks.append(
                    {
                        "name": "WM_BASE_URL",
                        "status": "ok",
                        "url": wm_base,
                    }
                )
            else:
                checks.append(
                    {
                        "name": "WM_BASE_URL",
                        "status": "unreachable",
                        "message": f"WorldMonitor returned HTTP {status_code}",
                    }
                )
        except urllib.error.HTTPError as exc:
            checks.append(
                {
                    "name": "WM_BASE_URL",
                    "status": "http_error" if exc.code >= 500 else "ok",
                    "message": f"HTTP {exc.code}" if exc.code >= 500 else "rejected",
                }
            )
        except Exception as exc:
            checks.append(
                {
                    "name": "WM_BASE_URL",
                    "status": "unreachable",
                    "message": f"Connection failed: {type(exc).__name__}",
                }
            )

    # 2. PUBLIC_API_SECRET_KEY (read-only fallback is acceptable)
    pub_key = os.environ.get("PUBLIC_API_SECRET_KEY", "").strip()
    if pub_key:
        checks.append({"name": "PUBLIC_API_SECRET_KEY", "status": "set"})
    else:
        finnhub = os.environ.get("FINNHUB_API_KEY", "").strip()
        checks.append(
            {
                "name": "PUBLIC_API_SECRET_KEY",
                "status": "missing",
                "message": "Public.com key not set. Read-only mode requires FINNHUB_API_KEY or EIA_API_KEY as fallback.",
                "fallback_available": bool(finnhub),
            }
        )

    # 3. Optional fallback keys
    for var in ("FINNHUB_API_KEY", "EIA_API_KEY"):
        val = os.environ.get(var, "").strip()
        checks.append({
            "name": var,
            "status": "set" if val else "missing",
        })

    # 4. EXECUTION_ENABLED gate
    exec_env = os.environ.get("EXECUTION_ENABLED", "").strip().lower() == "true"
    checks.append(
        {
            "name": "EXECUTION_ENABLED",
            "status": "enabled" if exec_env else "disabled",
            "message": "Live order submission is DISABLED (safe default). Set EXECUTION_ENABLED=true to enable."
            if not exec_env
            else "WARNING: Live order submission is ENABLED.",
        }
    )

    all_ok = all(c["status"] in ("ok", "set", "disabled") for c in checks)

    payload = {
        "ok": all_ok,
        "agent": "agent-oculus",
        "version": "0.3.0",
        "checks": checks,
    }
    return json.dumps(payload, indent=2)
