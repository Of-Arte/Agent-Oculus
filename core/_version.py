"""Shared version and profile-root resolution for the oculus plugin and core.

This module is deliberately dependency-free (stdlib only) so it can be
imported by both the Hermes plugin shim (plugins/oculus/) and the core
engine (core/) without creating circular imports.

Profile root resolution: when installed as a Hermes profile, the core/
package lives at ~/.hermes/profiles/oculus-test/core/. The profile root
(containing config.yaml, VERSION, core/) is two levels up from
this file: core/_version.py → core/ → profiles/oculus-test/.

REPO_ROOT env var overrides for development.
"""
from __future__ import annotations

import os
from pathlib import Path

_AGENT_NAME = "agent-oculus"


def get_version() -> str:
    """Read version from the VERSION file in the profile root."""
    return _read_version_file()

def get_agent_name() -> str:
    """Return the canonical agent/identifier name."""
    return _AGENT_NAME

def _profile_root_from_module() -> Path | None:
    """Locate the profile root from this module's file path.

    When installed: core/_version.py → core/ → profile_root/
    So profile_root = Path(__file__).resolve().parent.parent
    """
    here = Path(__file__).resolve()
    # core/_version.py → parent=core/, parent.parent=profile_root
    candidate = here.parent.parent
    if (candidate / "VERSION").exists() or (candidate / "config.yaml").exists():
        return candidate
    return None

def _read_version_file() -> str:
    """Read VERSION file, trying profile root then repo root."""
    # Try profile root (installed: core/_version.py → profile root is 2 levels up)
    profile_root = _profile_root_from_module()
    if profile_root is not None:
        version_file = profile_root / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()

    # Try REPO_ROOT env var (dev/test override)
    repo_root = os.environ.get("REPO_ROOT")
    if repo_root:
        version_file = Path(repo_root) / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()

    # Try cwd (running from repo root)
    version_file = Path.cwd() / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()

    return "0.0.0"


def get_profile_root() -> Path:
    """Find the profile root directory containing config.yaml.

    Used by load_config() and other components that need to locate
    profile-level files independent of cwd.

    Resolution order:
      1. REPO_ROOT env var (dev/test override)
      2. Profile root from this module's file path (installed plugin)
      3. cwd (fallback when running from repo root)
    """
    # REPO_ROOT env var overrides for dev/test
    env_root = os.environ.get("REPO_ROOT")
    if env_root:
        p = Path(env_root)
        if (p / "config.yaml").exists():
            return p

    # Installed profile: core/_version.py → profile root is 2 levels up
    profile_root = _profile_root_from_module()
    if profile_root is not None and (profile_root / "config.yaml").exists():
        return profile_root

    # Fallback: look up from cwd
    cwd = Path.cwd()
    if (cwd / "config.yaml").exists():
        return cwd

    # Last resort: return where we expect the profile root to be
    if profile_root is not None:
        return profile_root
    return Path.cwd()
