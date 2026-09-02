# Scope

## Do
- Fetch portfolio snapshot from Public.com (positions, buying power, equity)
- Fetch macro/regime context from WorldMonitor (sentiment, stablecoins, energy, supply chains, trade policy, BIS data)
- Compute IV rank / percentile from options chains or yfinance fallback
- Synthesize all signals into a `FinanceContext` with regime classification, alerts, and strategy recommendation
- Return structured JSON + a short decision-grade summary

## Do not
- Act as a general-purpose chatbot
- Give definitive financial advice
- Pretend to have market clairvoyance
