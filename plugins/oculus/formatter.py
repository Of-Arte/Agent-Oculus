"""Legacy formatter shim.

The active runtime uses core.output.formatter directly.
This module is left in place only so stale imports fail less loudly.
"""

from __future__ import annotations

from core.output.formatter import format_for_hermes
