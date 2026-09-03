from __future__ import annotations

from core.schemas import Alert, FinanceContext, NormalizedSignal, generate_alert_id, utc_now_iso


ETF_FLOW_REVERSAL_THRESHOLD = 100_000_000.0


def _is_stablecoin_alert(stablecoin) -> bool:
    return bool(getattr(stablecoin, 'is_depegged', False))


def _is_chokepoint_alert(chokepoint) -> bool:
    return float(getattr(chokepoint, 'score', 0) or 0) > 70


def _is_iv_rank_alert(chain) -> bool:
    iv = getattr(chain, 'iv_rank', None)
    return iv is not None and float(iv) > 70


def build_normalized_signals(context: FinanceContext) -> list[NormalizedSignal]:
    """Builds a list of normalized signals from the given finance context.

    Extracts relevant data points (such as market radar verdict, fear and greed index,
    stablecoin status, chokepoint disruptions, and options IV rank) and standardizes them
    into a unified signal format for easier analysis.

    An Alert supersedes its Signal per CONTEXT.md: when a data point breaches
    an alert threshold (stablecoin depeg, chokepoint score >70, IV rank >70),
    no Signal is emitted for that point — the Alert is the canonical representation.

    Args:
        context (FinanceContext): The aggregated financial and macroeconomic context.

    Returns:
        list[NormalizedSignal]: A list of signals normalized to a standard schema.
    """
    signals: list[NormalizedSignal] = []
    if context.market_radar is not None:
        signals.append(
            NormalizedSignal(
                signal_id='market-radar-verdict',
                category='macro',
                source='worldmonitor',
                label='Market radar verdict',
                state='bullish' if context.market_radar.verdict == 'BUY' else 'bearish',
                score=(context.market_radar.bullish_count / context.market_radar.total_known) if context.market_radar.total_known else 0.0,
                confidence=0.8,
                observed_at=context.market_radar.timestamp,
                value=context.market_radar.verdict,
            )
        )
    if context.fear_greed is not None:
        signals.append(
            NormalizedSignal(
                signal_id='fear-greed',
                category='market',
                source='worldmonitor',
                label='Fear and Greed',
                state='bullish' if context.fear_greed.value > 55 else 'bearish' if context.fear_greed.value < 50 else 'neutral',
                score=context.fear_greed.value / 100.0,
                confidence=0.8,
                observed_at=context.fear_greed.timestamp,
                value=context.fear_greed.value,
            )
        )
    for stablecoin in context.stablecoins or []:
        if _is_stablecoin_alert(stablecoin):
            continue
        signals.append(
            NormalizedSignal(
                signal_id=f'stablecoin-{stablecoin.symbol.lower()}',
                category='stablecoin',
                source='worldmonitor',
                label=f'Stablecoin {stablecoin.symbol}',
                state='bearish' if stablecoin.is_depegged else 'neutral',
                score=min(1.0, abs(stablecoin.peg_deviation_pct) / 5.0),
                confidence=0.85,
                observed_at=context.timestamp,
                value=stablecoin.peg_deviation_pct,
                symbol=stablecoin.symbol,
                metadata=stablecoin.to_dict(),
            )
        )
    for chokepoint in context.chokepoints or []:
        if _is_chokepoint_alert(chokepoint):
            continue
        signals.append(
            NormalizedSignal(
                signal_id=f'chokepoint-{chokepoint.name.lower().replace(" ", "-")}',
                category='supply_chain',
                source='worldmonitor',
                label=chokepoint.name,
                state='bearish' if chokepoint.score > 70 else 'neutral',
                score=min(1.0, chokepoint.score / 100.0),
                confidence=0.8,
                observed_at=context.timestamp,
                value=chokepoint.score,
                metadata=chokepoint.to_dict(),
            )
        )
    for ticker, chain in context.options_chains.items():
        if chain.iv_rank is not None:
            if _is_iv_rank_alert(chain):
                continue
            signals.append(
                NormalizedSignal(
                    signal_id=f'iv-rank-{ticker.lower()}',
                    category='options',
                    source='public',
                    label=f'IV rank {ticker}',
                    state='bearish' if chain.iv_rank > 70 else 'neutral',
                    score=min(1.0, chain.iv_rank / 100.0),
                    confidence=0.75,
                    observed_at=context.timestamp,
                    value=chain.iv_rank,
                    symbol=ticker,
                    metadata=chain.to_dict(),
                )
            )
    return signals


def evaluate_alerts(context: FinanceContext) -> list[Alert]:
    """Evaluates the finance context to generate actionable alerts.

    Scans the context for critical thresholds, such as elevated IV ranks, 
    stablecoin depegs, severe supply chain chokepoint disruptions, 
    regime changes, and significant ETF outflow reversals. 

    Args:
        context (FinanceContext): The aggregated financial and macroeconomic context.

    Returns:
        list[Alert]: A list of generated alerts with appropriate severities.
    """
    alerts: list[Alert] = []

    for ticker, chain in context.options_chains.items():
        if chain.iv_rank is None or chain.iv_rank <= 70:
            continue
        severity = 'CRITICAL' if chain.iv_rank > 85 else 'WARNING'
        alerts.append(Alert(
            alert_id=generate_alert_id(),
            alert_type='IV_RANK_HIGH',
            ticker=ticker,
            value=chain.iv_rank,
            threshold=70.0,
            direction='BEARISH',
            severity=severity,
            message=f'{ticker} IV rank is elevated at {chain.iv_rank:.2f}.',
            timestamp=context.timestamp,
        ))

    for stablecoin in context.stablecoins or []:
        if stablecoin.is_depegged:
            alerts.append(Alert(
                alert_id=generate_alert_id(),
                alert_type='STABLECOIN_DEPEG',
                ticker=stablecoin.symbol,
                value=abs(stablecoin.peg_deviation_pct),
                threshold=0.5,
                direction='BEARISH',
                severity='CRITICAL',
                message=f'{stablecoin.symbol} is depegged by {stablecoin.peg_deviation_pct:.2f}%.',
                timestamp=context.timestamp,
            ))

    for chokepoint in context.chokepoints or []:
        if chokepoint.score <= 70:
            continue
        severity = 'CRITICAL' if chokepoint.score > 85 else 'WARNING'
        alerts.append(Alert(
            alert_id=generate_alert_id(),
            alert_type='CHOKEPOINT_ALERT',
            ticker=None,
            value=chokepoint.score,
            threshold=70.0,
            direction='BEARISH',
            severity=severity,
            message=f'{chokepoint.name} disruption score is {chokepoint.score:.1f}.',
            timestamp=context.timestamp,
        ))

    alerts.append(Alert(
        alert_id=generate_alert_id(),
        alert_type='REGIME_CHANGE',
        ticker=None,
        value=0.0,
        threshold=0.0,
        direction='NEUTRAL',
        severity='INFO',
        message=f'Regime is {context.regime}.',
        timestamp=context.timestamp,
    ))

    for etf in context.etf_flows or []:
        if etf.flow_direction == 'OUTFLOW' and etf.flow_magnitude > ETF_FLOW_REVERSAL_THRESHOLD:
            alerts.append(Alert(
                alert_id=generate_alert_id(),
                alert_type='ETF_FLOW_REVERSAL',
                ticker=etf.ticker,
                value=etf.flow_magnitude,
                threshold=ETF_FLOW_REVERSAL_THRESHOLD,
                direction='BEARISH',
                severity='WARNING',
                message=f'{etf.ticker} flow reversal detected with outflow magnitude {etf.flow_magnitude:.0f}.',
                timestamp=context.timestamp,
            ))
    return alerts
