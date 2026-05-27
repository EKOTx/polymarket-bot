"""
test_connection.py - Test public Polymarket API connectivity.

Run this first to verify everything works before running main.py.

Usage:
    python scripts/test_connection.py
"""

import sys
import os
import json

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests


GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"

TIMEOUT = 10


def test_gamma_markets():
    """Test fetching market list from Gamma API."""
    print("\n=== TEST 1: Gamma API - Market List ===")
    url = f"{GAMMA_API}/markets"
    params = {"active": "true", "closed": "false", "limit": 5}

    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        markets = resp.json()

        print(f"✓ Connected to Gamma API")
        print(f"✓ Got {len(markets)} markets\n")

        for i, market in enumerate(markets[:5], 1):
            question = market.get("question", "No question")
            liquidity = market.get("liquidity", "N/A")
            volume = market.get("volume", "N/A")

            # Parse outcomes
            outcomes_raw = market.get("outcomes")
            prices_raw = market.get("outcomePrices")
            clob_ids_raw = market.get("clobTokenIds")

            outcomes = json.loads(outcomes_raw) if outcomes_raw else []
            prices = json.loads(prices_raw) if prices_raw else []
            clob_ids = json.loads(clob_ids_raw) if clob_ids_raw else []

            print(f"  Market {i}: {question[:70]}")
            print(f"    Liquidity: ${float(liquidity or 0):,.0f}")
            print(f"    Volume:    ${float(volume or 0):,.0f}")
            print(f"    Outcomes:  {list(zip(outcomes, prices))}")
            print(f"    CLOB IDs:  {clob_ids[:2]}{'...' if len(clob_ids) > 2 else ''}")
            print()

        return markets

    except requests.exceptions.ConnectionError:
        print("✗ Connection failed - check internet connection")
    except requests.exceptions.Timeout:
        print(f"✗ Timeout after {TIMEOUT}s")
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP {e.response.status_code}: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

    return []


def test_clob_orderbook(token_id: str, label: str = ""):
    """Test fetching order book from CLOB API."""
    print(f"\n=== TEST 2: CLOB API - Order Book ({label}) ===")
    url = f"{CLOB_API}/book"
    params = {"token_id": token_id}

    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        book = resp.json()

        bids = book.get("bids", [])
        asks = book.get("asks", [])

        print(f"✓ Connected to CLOB API")
        print(f"✓ Order book for token: {token_id[:20]}...")
        print(f"  Bids: {len(bids)} levels")
        print(f"  Asks: {len(asks)} levels")

        if bids:
            best_bid = max(float(b["price"]) for b in bids)
            print(f"  Best bid: {best_bid:.4f} ({best_bid*100:.1f}%)")

        if asks:
            best_ask = min(float(a["price"]) for a in asks)
            print(f"  Best ask: {best_ask:.4f} ({best_ask*100:.1f}%)")

        return True

    except requests.exceptions.ConnectionError:
        print("✗ Connection failed")
    except requests.exceptions.Timeout:
        print(f"✗ Timeout after {TIMEOUT}s")
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP {e.response.status_code}: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

    return False


def test_clob_health():
    """Test CLOB API health endpoint."""
    print("\n=== TEST 3: CLOB API Health ===")
    try:
        resp = requests.get(f"{CLOB_API}/", timeout=TIMEOUT)
        print(f"✓ CLOB API responded with status {resp.status_code}")
        return True
    except Exception as e:
        print(f"✗ CLOB API health check failed: {e}")
        return False


def main():
    print("=" * 60)
    print("POLYMARKET CONNECTION TEST")
    print("=" * 60)

    # Test 1: Gamma market list
    markets = test_gamma_markets()

    # Test 2: CLOB health
    test_clob_health()

    # Test 3: CLOB order book (use first market's token if available)
    if markets:
        for market in markets:
            clob_ids_raw = market.get("clobTokenIds")
            if clob_ids_raw:
                try:
                    clob_ids = json.loads(clob_ids_raw)
                    if clob_ids:
                        question = market.get("question", "")[:40]
                        test_clob_orderbook(clob_ids[0], label=f"YES token for: {question}")
                        break
                except (json.JSONDecodeError, TypeError):
                    pass

    print("\n=== SUMMARY ===")
    if markets:
        print(f"✓ Gamma API working - can fetch market data")
        print(f"  Ready to run: python main.py")
    else:
        print("✗ Could not fetch markets - check connection and try again")

    print("\nNote: Scanner uses public endpoints only.")
    print("No API key needed for scanning. .env is optional.\n")


if __name__ == "__main__":
    main()
