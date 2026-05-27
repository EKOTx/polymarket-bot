"""Market Analysis — spread, liquidity, vig ranking."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from database.db import init_db, get_session
from database.models import PriceSnapshot, Market as DBMarket

st.set_page_config(page_title="Market Analysis | Polymarket Quant", layout="wide", page_icon="📈")
init_db()


@st.cache_data(ttl=15)
def load_latest_snapshots() -> pd.DataFrame:
    """Load most recent price snapshot per market (YES only)."""
    with get_session() as s:
        # Get latest scan_id
        from sqlalchemy import func
        latest_scan = s.query(func.max(PriceSnapshot.scan_id)).scalar()
        if not latest_scan:
            return pd.DataFrame()

        rows = (
            s.query(PriceSnapshot, DBMarket)
            .join(DBMarket, PriceSnapshot.market_id == DBMarket.id)
            .filter(
                PriceSnapshot.scan_id == latest_scan,
                PriceSnapshot.outcome == "Yes",
            )
            .all()
        )
        if not rows:
            return pd.DataFrame()

        return pd.DataFrame([{
            "Market ID": snap.market_id,
            "Question": mkt.question[:65],
            "Event": mkt.event_title[:40],
            "Liquidity": mkt.liquidity,
            "Volume": mkt.volume,
            "YES Bid": snap.bid,
            "YES Ask": snap.ask,
            "YES Mid": snap.mid,
            "Spread": snap.spread,
            "Spread %": snap.spread_pct,
            "Bid Depth $": snap.bid_depth_usd,
            "Ask Depth $": snap.ask_depth_usd,
            "Source": snap.price_source,
        } for snap, mkt in rows])


@st.cache_data(ttl=15)
def load_price_history(market_id: str, hours: int = 6) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    with get_session() as s:
        rows = (
            s.query(PriceSnapshot)
            .filter(
                PriceSnapshot.market_id == market_id,
                PriceSnapshot.timestamp >= cutoff,
            )
            .order_by(PriceSnapshot.timestamp)
            .all()
        )
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "time": r.timestamp,
            "outcome": r.outcome,
            "bid": r.bid,
            "ask": r.ask,
            "mid": r.mid,
            "spread_pct": r.spread_pct,
        } for r in rows])


# ── Main ─────────────────────────────────────────────────────────────────────

st.markdown("# 📈 Market Analysis")

df = load_latest_snapshots()

if df.empty:
    st.info("No market data yet. Start the scanner to populate.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric("Markets", len(df))
c2.metric("Avg Spread %", f"{df['Spread %'].mean():.2f}%")
c3.metric("Total Liquidity", f"${df['Liquidity'].sum():,.0f}")
c4.metric("CLOB priced", f"{(df['Source']=='clob').sum()}/{len(df)}")

st.markdown("---")

tabs = st.tabs(["🏆 Top Liquidity", "📐 Widest Spreads", "🔍 Market Deep-Dive", "📊 Distributions"])

# ── Top liquidity ─────────────────────────────────────────────────────────────

with tabs[0]:
    st.markdown("### Highest Liquidity Markets")
    top_liq = df.sort_values("Liquidity", ascending=False).head(30).copy()
    top_liq["Liquidity"] = top_liq["Liquidity"].apply(lambda x: f"${x:,.0f}")
    top_liq["Volume"] = top_liq["Volume"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(
        top_liq[["Event", "Question", "YES Mid", "Spread %", "Liquidity", "Volume", "Source"]],
        use_container_width=True, height=500, hide_index=True,
    )

# ── Widest spreads ────────────────────────────────────────────────────────────

with tabs[1]:
    st.markdown("### Widest Spreads (potential market maker absence)")
    wide = df[df["Spread %"].notna()].sort_values("Spread %", ascending=False).head(30).copy()
    wide["Liquidity"] = wide["Liquidity"].apply(lambda x: f"${x:,.0f}")

    fig = px.bar(
        wide.head(20),
        x="Spread %",
        y="Question",
        orientation="h",
        color="Spread %",
        color_continuous_scale="RdYlGn_r",
        template="plotly_dark",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=500, margin=dict(l=0, r=0, t=10, b=0),
        yaxis_title=None,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        wide[["Event", "Question", "YES Bid", "YES Ask", "Spread %", "Liquidity"]],
        use_container_width=True, height=300, hide_index=True,
    )

# ── Market deep-dive ──────────────────────────────────────────────────────────

with tabs[2]:
    st.markdown("### Market Price History")
    search = st.text_input("Search market:", placeholder="Type to filter...")
    filtered = df[df["Question"].str.contains(search, case=False)] if search else df

    if filtered.empty:
        st.warning("No markets match search.")
    else:
        selected = st.selectbox("Select market:", filtered["Question"].tolist())
        market_id = filtered[filtered["Question"] == selected].iloc[0]["Market ID"]

        hours = st.slider("History (hours)", 1, 24, 6)
        hist = load_price_history(market_id, hours)

        if hist.empty:
            st.info("No price history for this market in the selected window.")
        else:
            yes_h = hist[hist["outcome"] == "Yes"]
            no_h = hist[hist["outcome"] == "No"]

            fig = go.Figure()
            if not yes_h.empty:
                fig.add_trace(go.Scatter(x=yes_h["time"], y=yes_h["mid"], name="YES mid",
                    line=dict(color="#00ff88", width=2)))
                fig.add_trace(go.Scatter(x=yes_h["time"], y=yes_h["bid"], name="YES bid",
                    line=dict(color="#00cc66", width=1, dash="dot")))
                fig.add_trace(go.Scatter(x=yes_h["time"], y=yes_h["ask"], name="YES ask",
                    line=dict(color="#00cc66", width=1, dash="dot"),
                    fill="tonexty", fillcolor="rgba(0,255,136,0.05)"))
            if not no_h.empty:
                fig.add_trace(go.Scatter(x=no_h["time"], y=no_h["mid"], name="NO mid",
                    line=dict(color="#f85149", width=2)))

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=350, margin=dict(l=0, r=0, t=10, b=0),
                yaxis_title="Price", xaxis_title=None,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Spread history
            if not yes_h.empty and "spread_pct" in yes_h.columns:
                fig2 = px.line(yes_h, x="time", y="spread_pct",
                    title="YES Spread %", template="plotly_dark",
                    color_discrete_sequence=["#f0883e"])
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    height=180, margin=dict(l=0, r=0, t=30, b=0),
                )
                st.plotly_chart(fig2, use_container_width=True)

# ── Distributions ─────────────────────────────────────────────────────────────

with tabs[3]:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Spread % Distribution**")
        sp_df = df[df["Spread %"].notna() & (df["Spread %"] < 20)]
        fig = px.histogram(sp_df, x="Spread %", nbins=40,
            color_discrete_sequence=["#00ff88"], template="plotly_dark")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=250, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Liquidity Distribution (log scale)**")
        import numpy as np
        liq_df = df[df["Liquidity"] > 0].copy()
        liq_df["log_liq"] = np.log10(liq_df["Liquidity"])
        fig = px.histogram(liq_df, x="log_liq", nbins=40,
            labels={"log_liq": "log10(Liquidity)"},
            color_discrete_sequence=["#388bfd"], template="plotly_dark")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=250, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
