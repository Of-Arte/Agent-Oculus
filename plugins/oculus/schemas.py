"""Tool input schemas for the oculus plugin.

These schemas are discovered by Hermes before register() is called, so they
must not import anything from core/.
"""

from __future__ import annotations

OCULUS_GET_CONTEXT = {
    "name": "oculus_get_context",
    "description": (
        "Build a full finance context signal: portfolio snapshot (Public.com), "
        "macro/regime (WorldMonitor), IV analysis, alerts, and a strategy "
        "recommendation. Returns structured JSON. Degrades gracefully when "
        "services are unavailable."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Optional list of tickers to filter signals/alerts to. "
                    "If omitted, context is built for portfolio positions + defaults."
                ),
            },
        },
    },
}

OCULUS_HEALTHCHECK = {
    "name": "oculus_healthcheck",
    "description": (
        "Validate environment config and service availability for the oculus "
        "profile (Public.com auth, WorldMonitor reachability, fallback providers)."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}
