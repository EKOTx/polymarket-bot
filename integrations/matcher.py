"""
Cross-platform market matcher.

Aligns Polymarket outcomes to external platform outcomes using fuzzy string
matching. Returns ValueSignal objects when PM price diverges from external
fair probability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

from integrations.normalizer import ExternalMarketOdds
from models.market import MarketData

# Minimum similarity to consider two markets the same
MATCH_THRESHOLD = 0.68
# Minimum token overlap ratio (Jaccard-like)
MIN_TOKEN_OVERLAP = 0.20
# Min edge % to surface as VALUE opportunity
MIN_VALUE_EDGE_PCT = 1.5
# Max mid price to consider (very high-prob outcomes have small edges)
MAX_MID = 0.97


_STOP_WORDS = frozenset({
    "will", "who", "what", "which", "the", "a", "an", "be", "is", "are",
    "in", "of", "to", "for", "on", "at", "by", "or", "and", "win", "wins",
    "2024", "2025", "2026", "2027", "2028",
    "presidential", "election", "nominee", "nomination",
    "market", "contract",
})


@dataclass
class MatchResult:
    pm_market: MarketData
    external: ExternalMarketOdds
    similarity: float
    pm_mid: float
    external_fair: float
    edge_pct: float            # (external_fair - pm_ask) * 100 if PM underpriced
    direction: str             # "BUY_YES" | "BUY_NO" | "NONE"


def _tokenize(text: str) -> str:
    """Lowercase, strip punctuation, remove stop words."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t not in _STOP_WORDS and len(t) > 1]
    return " ".join(tokens)


def _similarity(a: str, b: str) -> float:
    """
    Fuzzy string similarity after tokenization.
    Uses SequenceMatcher on token strings + Jaccard token overlap.
    Returns 0 if token overlap is below MIN_TOKEN_OVERLAP.
    """
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta or not tb:
        return 0.0

    set_a = set(ta.split())
    set_b = set(tb.split())
    if not set_a or not set_b:
        return 0.0

    jaccard = len(set_a & set_b) / len(set_a | set_b)
    if jaccard < MIN_TOKEN_OVERLAP:
        return 0.0

    seq_score = SequenceMatcher(None, ta, tb).ratio()
    # Blend: weight seq_score higher but require token overlap
    return round(seq_score * 0.7 + jaccard * 0.3, 4)


def _best_match(
    pm_title: str,
    candidates: list[ExternalMarketOdds],
) -> Optional[tuple[ExternalMarketOdds, float]]:
    """Return (best_match, similarity) or None if below threshold."""
    best: Optional[ExternalMarketOdds] = None
    best_score = 0.0

    for ext in candidates:
        score = _similarity(pm_title, ext.title)
        if score > best_score:
            best_score = score
            best = ext

    if best is None or best_score < MATCH_THRESHOLD:
        return None
    return best, best_score


def match_markets(
    pm_markets: list[MarketData],
    external: list[ExternalMarketOdds],
) -> list[MatchResult]:
    """
    Match each Polymarket market to best external outcome.

    Returns MatchResult for every match above threshold,
    regardless of edge (caller filters).
    """
    results: list[MatchResult] = []

    for pm in pm_markets:
        if pm.yes_mid is None or pm.yes_ask is None:
            continue
        if not (0.02 < pm.yes_mid < MAX_MID):
            continue

        match = _best_match(pm.question or "", external)
        if match is None:
            continue

        ext, sim = match
        fair = ext.fair_probability
        if fair is None:
            fair = ext.mid

        pm_ask = pm.yes_ask
        pm_bid = pm.yes_bid or 0.0
        pm_mid = pm.yes_mid

        # Edge: how much cheaper is PM than external fair value?
        # Positive = PM underpriced vs external (BUY PM)
        # Negative = PM overpriced vs external (ignore or sell, not implemented)
        edge_pct = (fair - pm_ask) * 100
        direction = "NONE"

        if edge_pct >= MIN_VALUE_EDGE_PCT:
            direction = "BUY_YES"
        elif (1 - fair) - (1 - pm_bid) >= MIN_VALUE_EDGE_PCT / 100:
            # No-side edge: external implies NO is underpriced on PM
            direction = "BUY_NO"

        results.append(MatchResult(
            pm_market=pm,
            external=ext,
            similarity=round(sim, 3),
            pm_mid=round(pm_mid, 4),
            external_fair=round(fair, 4),
            edge_pct=round(edge_pct, 2),
            direction=direction,
        ))

    # Sort: biggest YES edge first
    results.sort(key=lambda r: -r.edge_pct)
    return results


def filter_actionable(matches: list[MatchResult]) -> list[MatchResult]:
    """Return only matches where direction != NONE."""
    return [m for m in matches if m.direction != "NONE"]


def match_summary(matches: list[MatchResult]) -> dict:
    """Quick stats for logging."""
    actionable = filter_actionable(matches)
    return {
        "total_matches": len(matches),
        "actionable": len(actionable),
        "top_edge_pct": matches[0].edge_pct if matches else 0,
        "platforms": list({m.external.platform for m in matches}),
    }
