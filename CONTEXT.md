# CONTEXT.md — Agent Oculus Ubiquitous Language

Single context: finance context synthesis. Glossary only — no implementation details.

## Portfolio Domain

- **Position** — A single holding of an asset (symbol, quantity, market value, average cost). The atomic unit of portfolio exposure.
- **Portfolio View** — The consolidated broker snapshot for one account: buying power, cash, equity, and the set of Positions. Point-in-time.
- **Quote** — The latest market price observation for a symbol (price, change, timestamp).
- **Options Chain** — The set of option contracts for one underlying symbol at available expirations. Includes contract Greeks and implied volatility where available.
- **Option Contract** — A single put or call: underlying, expiration, strike, side, bid/ask/last, and Greeks (delta, gamma, theta, vega, rho, iv).

## Market Intelligence Domain

- **Macro Bundle** — The collection of WorldMonitor macro indicators fetched together (verdict, breadth, signals). A source-level bundle, not a single actionable item.
- **Radar Component** — One constituent indicator inside a Market Radar Verdict (e.g., moving average, breadth). Has a value and a bullish/bearish assessment.
- **Market Radar Verdict** — A consensus judgment over Radar Components: either BUY or CASH, with a count of bullish vs total known components.
- **Macro Verdict** — A free-form summary judgment carried inside a Macro Bundle. Distinct from Radar Verdict, which is a typed BUY/CASH.
- **Fear & Greed Index** — A 0–100 sentiment score with a classification label and timestamp.
- **Stablecoin Status** — Price, peg, and peg deviation for one stablecoin. A stablecoin is **Depegged** when absolute peg deviation exceeds 0.5%.
- **Exchange-Traded Fund Flow** — Net flow direction (INFLOW, OUTFLOW, NEUTRAL) and magnitude for one ETF ticker at a point in time.
- **Energy Prices** — Observed WTI and Brent prices with timestamp.
- **Chokepoint Status** — Disruption score and level (LOW, MEDIUM, HIGH, CRITICAL) for a named global supply-chain chokepoint (e.g., Strait of Hormuz).
- **Trade Restriction** — A policy restriction entry by country and type.
- **BIS Policy Rate** — A central bank policy rate by country with timestamp.

## Synthesis Domain

- **Signal** — A single normalized, categorized observation derived from a source data point. Has category (market, macro, portfolio, options, stablecoin, flow, supply_chain, trade_policy, risk), state (bullish, bearish, neutral, unknown), score, confidence, and observed time. The canonical actionable unit produced by synthesis. Formerly called NormalizedSignal in code.
- **Signal Category** — The classification of what a Signal describes (market, macro, portfolio, options, stablecoin, flow, supply_chain, trade_policy, risk).
- **Signal State** — The directional assessment of a Signal: bullish, bearish, neutral, or unknown.
- **Alert** — A threshold-triggered notification derived from the Synthesized Context. An Alert **supersedes** its originating Signal: when a data point breaches an alert threshold, the Alert is the canonical representation and the underlying Signal is suppressed (not emitted alongside it).
- **Alert Severity** — INFO, WARNING, or CRITICAL.
- **Alert Direction** — BULLISH, BEARISH, or NEUTRAL.
- **Finance Context (Raw)** — The aggregation of portfolio, market, and macro data before signal normalization and alert evaluation. A transient assembly stage.
- **Synthesized Context** — The enriched Finance Context after signal normalization, alert evaluation, regime classification, and IV rank computation. This is the sole deliverable returned to the caller and to the agent. Contains Signals (or their superseding Alerts), Market Regime, Volatility Regimes, and metadata.

## Regime & Volatility Domain

- **Market Regime** — The top-level macro risk appetite classification: RISK_ON, RISK_OFF, or TRANSITIONAL. Computed from Radar Verdict, Fear & Greed, chokepoint scores, and stablecoin peg health. TRANSITIONAL here means risk appetite is neither clearly on nor off.
- **Regime Flag** — An auxiliary risk marker attached to a Market Regime. Currently: MACRO_SHOCK_RISK (a chokepoint score exceeds 70) and LIQUIDITY_STRESS (a stablecoin is Depegged).
- **Volatility Regime** — The implied-volatility environment for one symbol: HIGH_VOLATILITY (IV Rank ≥ 60), MEDIUM_VOLATILITY (40–59), LOW_VOLATILITY (< 40), or TRANSITIONAL (rapid 10-day rank change exceeds 10 points, overriding the static bucket). Distinct from Market Regime; the two regimes are orthogonal.
- **IV Rank** — The position of current implied volatility within its lookback distribution (0–100). IV Percentile is the share of past observations below current IV.
- **Implied Volatility (IV)** — The market's forward-looking volatility expectation extracted from option prices (typically at-the-money).
- **Disruption Level** — Severity bucket for a Chokepoint Status: LOW, MEDIUM, HIGH, CRITICAL.

## Deprecated / Legacy

- **Account Snapshot** — Legacy alias for the account-level fields inside Portfolio View (account id, buying power, cash, equity without positions). Retained for compatibility but Portfolio View is canonical. Do not use for new concepts.
