"""
config.py - Load and validate environment settings.

All settings come from .env file. Defaults are safe (dry-run ON).
Never prints private keys.
"""

import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


def _get_bool(key: str, default: bool = True) -> bool:
    """Read boolean env var. Defaults to True (safe side)."""
    val = os.getenv(key, str(default)).strip().lower()
    return val in ("true", "1", "yes")


def _get_float(key: str, default: float) -> float:
    """Read float env var with fallback."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        print(f"[config] WARNING: Invalid value for {key}, using default {default}")
        return default


def _get_int(key: str, default: int) -> int:
    """Read int env var with fallback."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        print(f"[config] WARNING: Invalid value for {key}, using default {default}")
        return default


# ── Safety ─────────────────────────────────────────────────────────────────────
# DRY_RUN must default to True. Real trades only when explicitly disabled.
DRY_RUN: bool = _get_bool("DRY_RUN", default=True)

# ── Scanner settings ────────────────────────────────────────────────────────────
MIN_PROFIT_PERCENT: float = _get_float("MIN_PROFIT_PERCENT", default=1.0)
SCAN_INTERVAL_SECONDS: int = _get_int("SCAN_INTERVAL_SECONDS", default=10)
MIN_LIQUIDITY: float = _get_float("MIN_LIQUIDITY", default=1000.0)
MARKET_LIMIT: int = _get_int("MARKET_LIMIT", default=50)

# ── API credentials (optional - only for authenticated trading) ─────────────────
# These are NOT validated here - missing = scanner-only mode
POLYMARKET_API_KEY: str = os.getenv("POLYMARKET_API_KEY", "")
POLYMARKET_SECRET: str = os.getenv("POLYMARKET_SECRET", "")
POLYMARKET_PASSPHRASE: str = os.getenv("POLYMARKET_PASSPHRASE", "")
POLYMARKET_PRIVATE_KEY: str = os.getenv("POLYMARKET_PRIVATE_KEY", "")
WALLET_ADDRESS: str = os.getenv("WALLET_ADDRESS", "")

# ── API endpoints ───────────────────────────────────────────────────────────────
GAMMA_API_BASE: str = "https://gamma-api.polymarket.com"
CLOB_API_BASE: str = "https://clob.polymarket.com"

# ── Paper trading ───────────────────────────────────────────────────────────────
PAPER_STARTING_BALANCE: float = 1000.0  # USD


def has_api_credentials() -> bool:
    """Check if API credentials are configured (needed for real trading)."""
    return bool(POLYMARKET_API_KEY and POLYMARKET_SECRET and POLYMARKET_PASSPHRASE)


def print_config_summary():
    """Print current config (never prints secrets)."""
    print(f"  DRY_RUN:              {DRY_RUN}")
    print(f"  MIN_PROFIT_PERCENT:   {MIN_PROFIT_PERCENT}%")
    print(f"  SCAN_INTERVAL:        {SCAN_INTERVAL_SECONDS}s")
    print(f"  MIN_LIQUIDITY:        ${MIN_LIQUIDITY:,.0f}")
    print(f"  MARKET_LIMIT:         {MARKET_LIMIT}")
    print(f"  API credentials set:  {has_api_credentials()}")
    print(f"  Wallet set:           {bool(WALLET_ADDRESS)}")
