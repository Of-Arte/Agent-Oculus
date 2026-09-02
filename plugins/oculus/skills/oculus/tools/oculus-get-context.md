# oculus_get_context Tool Guide

## When to use
- User asks for market context, portfolio status, macro analysis, regime classification, or signal synthesis.
- Run this before providing any market commentary.

## Input
- `symbols` (optional, array of strings): Filter signals/alerts to specific tickers.
  If omitted, the agent builds context for portfolio positions + default symbols (SPY, QQQ, XLE).

## Output (JSON)
- `ok`: boolean
- `regime`: RISK_ON | RISK_OFF | TRANSITIONAL
- `regime_flags`: list of flag strings (e.g. MACRO_SHOCK_RISK, LIQUIDITY_STRESS, HIGH_VOLATILITY)
- `signals`: normalized signal objects (category, source, state, score, confidence)
- `alerts`: alert objects (type, severity, direction, message)
- `iv_analysis`: per-symbol IV rank, IV percentile, vol regime
- `summary`: position count, active symbols, fear/greed, verdict, depegged stablecoins, critical chokepoints

## Degraded Mode
- If Public.com credentials are absent: portfolio data empty, but macro + IV analysis still flow.
- If WorldMonitor is unreachable: macro fields are null, but portfolio + IV analysis still work.
- If both are down: returns an error JSON with `ok: false`.
