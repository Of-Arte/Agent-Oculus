"""oculus Hermes plugin.

Registers two coarse tools under the ``oculus`` toolset:

* ``oculus_get_context`` — full portfolio + macro + regime + IV + alerts synthesis
* ``oculus_healthcheck`` — env/config validation + service availability check

Plus a bundled skill ``oculus`` (doctrine) resolvable via ``oculus:oculus`` within
the oculus profile.

Hermes loads this plugin when enabled in the oculus profile's config.yaml:
  plugins.enabled: [oculus]

The plugin is installed to ~/.hermes/plugins/oculus/ by Hermes at install time.
The repo root (with core/, tools/) is copied to ~/.hermes/profiles/oculus/.
The sys.path bootstrap below lets the plugin import core/ modules from the
profile directory.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .schemas import OCULUS_GET_CONTEXT, OCULUS_HEALTHCHECK
from .tools import oculus_get_context, oculus_healthcheck


def _repo_root() -> str:
    """Find the profile directory (repo root) so core/ is importable.

    Hermes installs:
      - plugin package at ~/.hermes/plugins/oculus/
      - profile root at  ~/.hermes/profiles/oculus/  (has core/, tools/)

    We look up two levels from this file to find the profile root.
    REPO_ROOT env var overrides for dev/test.
    """
    here = Path(__file__).resolve().parent  # ~/.hermes/plugins/oculus/
    candidates = [
        here.parent.parent / "profiles" / "oculus",  # ~/.hermes/profiles/oculus/
    ]
    env_root = os.environ.get("REPO_ROOT")
    if env_root:
        candidates.insert(0, Path(env_root))
    for c in candidates:
        if (c / "core").is_dir():
            return str(c)
    # Fallback: also try the repo root from the working directory
    cwd = Path.cwd()
    if (cwd / "core").is_dir():
        return str(cwd)
    return str(here.parent.parent)


_REPO_ROOT = _repo_root()
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def register(ctx) -> None:
    """Register oculus tools and the bundled doctrine skill.

    Called by Hermes during plugin discovery. ctx provides register_tool()
    and register_skill() methods.
    """
    # Register coarse tools
    ctx.register_tool(
        name="oculus_get_context",
        toolset="oculus",
        schema=OCULUS_GET_CONTEXT,
        handler=oculus_get_context,
        emoji="📊",
    )

    ctx.register_tool(
        name="oculus_healthcheck",
        toolset="oculus",
        schema=OCULUS_HEALTHCHECK,
        handler=oculus_healthcheck,
        emoji="🔧",
    )

    # Register the bundled doctrine skill (opt-in via skill_view)
    skill_md = Path(__file__).resolve().parent / "skills" / "oculus" / "SKILL.md"
    if skill_md.exists():
        ctx.register_skill(
            name="oculus",
            path=skill_md,
            description="Agent Oculus identity, doctrine, operating rules, and tool guidance.",
        )
