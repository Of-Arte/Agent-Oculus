# WorldMonitor API Reference

## Configuration
- Base URL: `WM_BASE_URL` env var (e.g. `http://your-worldmonitor-host:8000`)
- Auth: `X-WorldMonitor-Key` header from `WORLDMONITOR_API_KEY` (optional - skipped if absent)

## Key Endpoints
- **Market Radar Verdict:** `GET /api/economic/v1/get-macro-signals`
  - Fields: `verdict` (BUY/CASH), `bullishCount`, `totalCount`, `signals`
- **Fear & Greed:** Available via market radar service
- **Stablecoins:** `GET` stablecoin markets - peg status, depeg detection
- **ETF Flows:** BTC ETF flow summaries (INFLOW/OUTFLOW/NEUTRAL)
- **Energy Prices:** WTI, Brent crude
- **Supply Chain Chokepoints:** Score + disruption level (LOW/MEDIUM/HIGH/CRITICAL)
- **Trade Policy:** Trade restrictions, tariff trends, trade flows
- **BIS Policy Rates:** Central bank policy rates per country

## Timeout
15 seconds default.
