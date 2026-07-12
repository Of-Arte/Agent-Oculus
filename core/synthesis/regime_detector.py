from __future__ import annotations

from dataclasses import dataclass

from core.schemas import ChokepointStatus, FearGreedIndex, MarketRadarVerdict, StablecoinStatus


@dataclass(slots=True)
class RegimeResult:
    """Represents the computed market regime and any associated risk flags.

    Attributes:
        regime (str): The calculated market regime (e.g., 'RISK_ON', 'RISK_OFF', 'TRANSITIONAL').
        flags (list[str]): A list of active risk flags (e.g., 'MACRO_SHOCK_RISK', 'LIQUIDITY_STRESS').
    """
    regime: str
    flags: list[str]

    def to_dict(self) -> dict[str, object]:
        """Converts the regime result into a dictionary representation.

        Returns:
            dict[str, object]: The dictionary containing 'regime' and 'flags'.
        """
        return {'regime': self.regime, 'flags': self.flags}


def detect_regime(
    verdict: MarketRadarVerdict,
    fear_greed: FearGreedIndex,
    chokepoints: list[ChokepointStatus],
    stablecoins: list[StablecoinStatus],
) -> RegimeResult:
    """Detects the current market regime based on macroeconomic and sentiment indicators.

    Evaluates the market radar verdict, fear and greed index, geopolitical chokepoints, 
    and stablecoin pegs to determine if the market is 'RISK_ON', 'RISK_OFF', or 'TRANSITIONAL'.
    Also identifies systemic risks like macro shocks and liquidity stress.

    Args:
        verdict (MarketRadarVerdict): The current market radar consensus.
        fear_greed (FearGreedIndex): The current fear and greed index reading.
        chokepoints (list[ChokepointStatus]): The status of critical global chokepoints.
        stablecoins (list[StablecoinStatus]): The status of major stablecoin pegs.

    Returns:
        RegimeResult: An object containing the computed regime and any identified risk flags.
    """
    if verdict.verdict == 'BUY' and fear_greed.value > 55 and verdict.bullish_count >= 5:
        regime = 'RISK_ON'
    elif verdict.verdict == 'CASH' and fear_greed.value < 50:
        regime = 'RISK_OFF'
    else:
        regime = 'TRANSITIONAL'

    flags: list[str] = []
    if any(item.score > 70 for item in chokepoints):
        flags.append('MACRO_SHOCK_RISK')
    if any(item.is_depegged for item in stablecoins):
        flags.append('LIQUIDITY_STRESS')
    return RegimeResult(regime=regime, flags=flags)
