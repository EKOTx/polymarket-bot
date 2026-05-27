"""
utils.py - Shared helper functions.
"""

import time
from datetime import datetime
from typing import Optional


def now_str() -> str:
    """Current time as HH:MM:SS string."""
    return datetime.now().strftime("%H:%M:%S")


def safe_float(value, default: float = 0.0) -> float:
    """Convert value to float, return default if conversion fails."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def percent(value: float) -> str:
    """Format float as percentage string: 0.73 → '73.0%'"""
    return f"{value * 100:.1f}%"


def usd(value: float) -> str:
    """Format float as USD string: 1234.5 → '$1,234.50'"""
    return f"${value:,.2f}"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def retry(func, retries: int = 3, delay: float = 2.0, label: str = ""):
    """
    Call func up to `retries` times. Return result or None on failure.
    Prints error on each failed attempt.
    """
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as e:
            tag = f"[{label}] " if label else ""
            print(f"{tag}Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    return None


def truncate(text: str, max_len: int = 60) -> str:
    """Truncate long strings for display."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
