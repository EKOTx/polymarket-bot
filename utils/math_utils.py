"""
Probability math utilities for prediction market analysis.
"""

from typing import Sequence


def devig_multiplicative(prices: Sequence[float]) -> list[float]:
    """
    Remove vig from a set of prices using multiplicative normalization.

    Divides each price by the sum so they add to 1.0.
    Fair value = price / sum(prices)

    Example: [0.55, 0.55] → [0.5, 0.5]
    """
    total = sum(prices)
    if total == 0:
        return list(prices)
    return [p / total for p in prices]


def devig_additive(prices: Sequence[float]) -> list[float]:
    """
    Remove vig using additive normalization.

    Subtracts equal share of excess from each price.
    Fair value = price - (sum - 1.0) / n
    """
    n = len(prices)
    if n == 0:
        return []
    total = sum(prices)
    excess_per = (total - 1.0) / n
    return [max(0.0, p - excess_per) for p in prices]


def vig_pct(prices: Sequence[float]) -> float:
    """Total vig as a percentage. 0% = no vig, 5% = 5% overround."""
    return (sum(prices) - 1.0) * 100


def implied_prob(american_odds: float) -> float:
    """Convert American odds to implied probability."""
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100)


def american_to_decimal(american_odds: float) -> float:
    """Convert American odds to decimal odds."""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


def decimal_to_implied_prob(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability."""
    if decimal_odds <= 0:
        return 0.0
    return 1.0 / decimal_odds


def kelly_fraction(
    win_prob: float,
    win_odds: float,      # decimal odds (e.g. 2.0 = evens)
    max_fraction: float = 0.25,
) -> float:
    """
    Full Kelly fraction. Returns fraction of bankroll to bet.

    f = (b*p - q) / b
    where b = decimal odds - 1, p = win prob, q = 1 - p

    Capped at max_fraction (default 25%) for safety.
    """
    b = win_odds - 1
    p = win_prob
    q = 1 - p
    if b <= 0:
        return 0.0
    f = (b * p - q) / b
    return max(0.0, min(f, max_fraction))


def half_kelly(win_prob: float, win_odds: float) -> float:
    """Half Kelly — more conservative, recommended for prediction markets."""
    return kelly_fraction(win_prob, win_odds) * 0.5


def edge_pct(fair_prob: float, market_ask: float) -> float:
    """
    Edge % when buying at market_ask with estimated fair probability.

    Edge = (fair_prob - market_ask) / market_ask * 100
    Positive = we're buying cheap (good).
    """
    if market_ask <= 0:
        return 0.0
    return ((fair_prob - market_ask) / market_ask) * 100


def confidence_score(
    edge: float,
    liquidity: float,
    spread_pct: float,
    source_quality: float = 1.0,
) -> float:
    """
    Composite confidence score 0-1 for an opportunity.

    Factors:
    - edge size (bigger = better)
    - liquidity (more = better)
    - spread width (tighter = better)
    - source quality (external odds quality)

    Returns 0-1 where 1 = maximum confidence.
    """
    # Normalize each factor to 0-1
    edge_score = min(edge / 10.0, 1.0)                  # 10% edge = max score
    liq_score = min(liquidity / 100_000, 1.0)            # $100k = max score
    spread_score = max(0.0, 1.0 - spread_pct / 10.0)    # 0% spread = max

    # Weighted combination
    score = (
        edge_score * 0.40
        + liq_score * 0.25
        + spread_score * 0.20
        + source_quality * 0.15
    )
    return round(min(1.0, max(0.0, score)), 3)


def slippage_estimate(
    size_usd: float,
    best_ask: float,
    depth_levels: list[dict],
) -> float:
    """
    Estimate slippage for a given USD trade size.

    Walks the order book until size_usd is filled.
    Returns average fill price vs best_ask.

    depth_levels: list of {"price": float, "size": float}
    """
    remaining = size_usd
    total_cost = 0.0

    for level in depth_levels:
        if remaining <= 0:
            break
        level_size_usd = level["price"] * level["size"]
        fill = min(remaining, level_size_usd)
        total_cost += fill * (level["price"] / best_ask)  # normalized
        remaining -= fill

    if size_usd == 0 or remaining == size_usd:
        return 0.0

    avg_fill = total_cost / (size_usd - remaining)
    return (avg_fill - 1.0) * 100  # slippage %
