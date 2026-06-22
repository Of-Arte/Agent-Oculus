"""Deprecated Oculus tool handlers.

The active project no longer ships the Hermes plugin/toolpack integration.
This module is kept inert for compatibility with stale imports.
"""

from __future__ import annotations

import json


def oculus_healthcheck(args: dict, **kwargs) -> str:
    return json.dumps(
        {
            "ok": False,
            "error": "Deprecated: Hermes skin/plugin integration has been removed from the active setup.",
        },
        indent=2,
    )


def oculus_get_context(args: dict, **kwargs) -> str:
    return json.dumps(
        {
            "ok": False,
            "error": "Deprecated: use the CLI runtime (python main.py --run-once) for context signals.",
            "symbols": args.get("symbols"),
        },
        indent=2,
    )
