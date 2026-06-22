"""Oculus Hermes plugin (profile-native, low-bloat toolpack)."""

from __future__ import annotations

from .tools import oculus_get_context, oculus_healthcheck


def register(ctx) -> None:
    ctx.register_tool(
        name="oculus_healthcheck",
        toolset="oculus",
        schema={
            "name": "oculus_healthcheck",
            "description": "Check Oculus profile health (profile home, env state, and enabled assets).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        handler=oculus_healthcheck,
        emoji="🧪",
    )
    ctx.register_tool(
        name="oculus_get_context",
        toolset="oculus",
        schema={
            "name": "oculus_get_context",
            "description": "Fetch portfolio + WorldMonitor macro context + derived signals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of ticker symbols to focus signals on.",
                    }
                },
                "required": [],
            },
        },
        handler=oculus_get_context,
        emoji="👁️",
    )
