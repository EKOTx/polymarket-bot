"""Settings viewer — shows current config (no secrets exposed)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Settings | Polymarket Quant", layout="wide", page_icon="⚙️")

st.markdown("# ⚙️ Settings")
st.caption("Read-only view. Edit `.env` to change settings. Never shows secret values.")


def masked(val: str) -> str:
    if not val:
        return "*(not set)*"
    return f"`{'*' * min(len(val), 8)}...`"


def bool_badge(val: str) -> str:
    v = val.lower()
    if v in ("true", "1", "yes"):
        return "🟢 **TRUE**"
    return "🔴 **FALSE**"


st.markdown("### 🛡️ Safety")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**ENABLE_REAL_TRADING:** {bool_badge(os.getenv('ENABLE_REAL_TRADING','false'))}")
    st.markdown(f"**DRY_RUN:** {bool_badge(os.getenv('DRY_RUN','true'))}")
with col2:
    st.warning("Real trading is NOT implemented. These flags prevent accidental activation.")

st.markdown("---")
st.markdown("### 🔍 Scanner")
cols = st.columns(3)
settings = [
    ("SCAN_INTERVAL_SECONDS", "30"),
    ("MARKET_LIMIT", "500"),
    ("MIN_LIQUIDITY", "500"),
    ("CLOB_CONCURRENCY", "15"),
    ("MIN_EDGE_PCT", "0.5"),
    ("MIN_VIG_PCT", "2.0"),
    ("MIN_CONFIDENCE", "0.4"),
    ("LOG_LEVEL", "INFO"),
]
for i, (k, default) in enumerate(settings):
    with cols[i % 3]:
        st.metric(k, os.getenv(k, default))

st.markdown("---")
st.markdown("### 💰 Paper Trading")
pcols = st.columns(3)
paper_settings = [
    ("PAPER_STARTING_BALANCE", "10000"),
    ("PAPER_MAX_POSITION_SIZE", "500"),
    ("PAPER_MAX_DAILY_LOSS", "1000"),
]
for i, (k, d) in enumerate(paper_settings):
    with pcols[i]:
        st.metric(k, f"${float(os.getenv(k, d)):,.0f}")

st.markdown("---")
st.markdown("### 🔑 API Credentials")
cred_settings = [
    ("POLYMARKET_API_KEY", "Polymarket API Key"),
    ("POLYMARKET_PRIVATE_KEY", "Polymarket Private Key"),
    ("THE_ODDS_API_KEY", "The Odds API Key"),
    ("KALSHI_API_KEY", "Kalshi API Key"),
    ("WALLET_ADDRESS", "Wallet Address"),
]
for k, label in cred_settings:
    val = os.getenv(k, "")
    status = "✅ set" if val else "❌ not set"
    st.markdown(f"**{label}** ({k}): {status}")

st.markdown("---")
st.markdown("### 🗄️ Infrastructure")
st.markdown(f"**DATABASE_URL:** `{os.getenv('DATABASE_URL','sqlite:///data/polymarket.db')}`")
st.markdown(f"**LOG_FILE:** `{os.getenv('LOG_FILE','logs/scanner.log')}`")
st.markdown(f"**GAMMA_API_BASE:** `{os.getenv('GAMMA_API_BASE','https://gamma-api.polymarket.com')}`")
st.markdown(f"**CLOB_API_BASE:** `{os.getenv('CLOB_API_BASE','https://clob.polymarket.com')}`")

st.markdown("---")
st.info("To change settings: edit `.env` in the project root and restart the scanner.")
