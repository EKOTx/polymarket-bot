import requests
import websocket
import json
import os
import time

price_history = {}

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

markets_url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=10"

response = requests.get(markets_url)
markets = response.json()

token_ids = []
asset_info = {}

for market in markets:

    question = market.get("question", "No question")

    token_ids_raw = market.get("clobTokenIds")

    if not token_ids_raw:
        continue

    market_token_ids = json.loads(token_ids_raw)
    outcomes = json.loads(market.get("outcomes", "[]"))

    for token_id, outcome in zip(market_token_ids, outcomes):

        token_ids.append(token_id)

        asset_info[token_id] = {
            "market": question,
            "outcome": outcome
        }

latest_prices = {}
last_draw = 0
DRAW_INTERVAL = 2

ws_url = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

def clear():
    print("\033[H\033[J", end="")

def draw_dashboard():

    clear()

    print("=" * 100)
    print("POLYMARKET LIVE TERMINAL")
    print("=" * 100)

    grouped = {}

    for asset_id, info in latest_prices.items():

        market = info["market"]
        outcome = info["outcome"]

        if market not in grouped:
            grouped[market] = {}

        grouped[market][outcome] = info

    for market, outcomes in grouped.items():

        print(f"\n{market}")

        yes_data = outcomes.get("Yes")
        no_data = outcomes.get("No")

        if yes_data:

            yes_mid = (
                yes_data["bid"] +
                yes_data["ask"]
            ) / 2

            yes_color = GREEN if yes_mid >= 0.5 else RED

            print(
                f"{yes_color}"
                f"YES  Bid {yes_data['bid']*100:.1f}% "
                f"| Ask {yes_data['ask']*100:.1f}%"
                f"{RESET}"
            )

        if no_data:

            no_mid = (
                no_data["bid"] +
                no_data["ask"]
            ) / 2

            no_color = GREEN if no_mid >= 0.5 else RED

            print(
                f"{no_color}"
                f"NO   Bid {no_data['bid']*100:.1f}% "
                f"| Ask {no_data['ask']*100:.1f}%"
                f"{RESET}"
            )

        print("-" * 100)

def on_open(ws):

    subscribe_message = {
        "assets_ids": token_ids,
        "type": "market"
    }

    ws.send(json.dumps(subscribe_message))

def on_message(ws, message):

    global last_draw

    data = json.loads(message)

    if isinstance(data, list):
        return

    if data.get("event_type") != "price_change":
        return

    updated = False

    for change in data.get("price_changes", []):

        asset_id = change.get("asset_id")

        best_bid = change.get("best_bid")
        best_ask = change.get("best_ask")

        if not best_bid or not best_ask:
            continue

        best_bid = float(best_bid)
        best_ask = float(best_ask)

        mid_price = (best_bid + best_ask) / 2

        old_price = price_history.get(asset_id)

        move = 0

        if old_price is not None:
            move = mid_price - old_price

        price_history[asset_id] = mid_price

        info = asset_info.get(asset_id)

        if not info:
            continue

        latest_prices[asset_id] = {
            "market": info["market"],
            "outcome": info["outcome"],
            "bid": best_bid,
            "ask": best_ask,
            "move": move
        }

        updated = True

    if updated and time.time() - last_draw >= DRAW_INTERVAL:
        draw_dashboard()
        last_draw = time.time()

def on_error(ws, error):
    print("ERROR:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

ws = websocket.WebSocketApp(
    ws_url,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()