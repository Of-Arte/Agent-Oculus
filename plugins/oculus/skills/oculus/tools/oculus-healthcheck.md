# oculus_healthcheck Tool Guide

## When to use
- First setup or after changing env vars.
- When the agent seems to be producing incomplete output.
- Before reporting "everything is broken" — this tool tells you exactly which service is down.

## Input
- None.

## Output (JSON)
- `ok`: boolean (true only if all required checks pass)
- `checks`: list of check objects:
  - `WM_BASE_URL`: ok / missing / unreachable — WorldMonitor reachability
  - `PUBLIC_API_SECRET_KEY`: set / missing — Public.com auth
  - `FINNHUB_API_KEY`: set / missing — optional fallback
  - `EIA_API_KEY`: set / missing — optional fallback

## Action
- Run this tool first if context output looks wrong or incomplete.
- Fix any "missing" or "unreachable" items before proceeding.
