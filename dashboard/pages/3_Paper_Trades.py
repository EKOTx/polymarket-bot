"""Paper Trades — simulated trade tracking and PnL."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from database.db import init_db, get_session
from database.models import PaperTrade as DBTrade, Portfolio as DBPortfolio

st.set_page_config(page_title="Paper Trades | Polymarket Quant", layout="wide", page_icon="🧾")
init_db()


@st.cache_data(ttl=10)
def load_trades() -> pd.DataFrame:
    with get_session() as s:
        rows = s.query(DBTrade).order_by(DBTrade.opened_at.desc()).limit(500).all()
        if not rows:
            return pd.DataFrame()
        records = []
        for r in rows:
            notes = json.loads(r.notes or "{}")
            records.append({
                "ID": r.id,
                "Status": r.status,
                "Strategy": r.strategy,
                "Question": r.question[:60],
                "Outcome": r.outcome,
                "Side": r.side,
                "Entry Price": r.entry_price,
                "Shares": r.size_shares,
                "Cost $": r.cost_usd,
                "Exit Price": r.exit_price,
                "Realized PnL": r.realized_pnl,
                "Unreal PnL": r.unrealized_pnl,
                "Edge % (at entry)": notes.get("edge_pct"),
                "Confidence": notes.get("confidence"),
                "Opened": r.opened_at,
                "Closed": r.closed_at,
            })
        return pd.DataFrame(records)


@st.cache_data(ttl=10)
def load_portfolio_history() -> pd.DataFrame:
    with get_session() as s:
        rows = s.query(DBPortfolio).order_by(DBPortfolio.timestamp).all()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "time": r.timestamp,
            "balance": r.balance,
            "realized_pnl": r.realized_pnl,
            "unrealized_pnl": r.unrealized_pnl,
            "total_trades": r.total_trades,
            "open_positions": r.open_positions,
        } for r in rows])


# ── Main ─────────────────────────────────────────────────────────────────────

st.markdown("# 🧾 Paper Trades")
st.caption("All simulated trades. No real money involved.")

df = load_trades()
port_hist = load_portfolio_history()

# ── KPIs ─────────────────────────────────────────────────────────────────────

if not df.empty:
    open_trades = df[df["Status"] == "OPEN"]
    closed_trades = df[df["Status"] == "CLOSED"]
    wins = closed_trades[closed_trades["Realized PnL"] > 0] if not closed_trades.empty else pd.DataFrame()
    total_pnl = closed_trades["Realized PnL"].sum() if not closed_trades.empty else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Trades", len(df))
    c2.metric("Open", len(open_trades))
    c3.metric("Closed", len(closed_trades))
    c4.metric("Win Rate", f"{len(wins)/max(len(closed_trades),1):.0%}")
    c5.metric("Realized PnL", f"${total_pnl:+,.2f}")
else:
    st.info("No paper trades yet. Scanner will execute trades when actionable opportunities are found.")
    st.stop()

st.markdown("---")

# ── PnL chart ─────────────────────────────────────────────────────────────────

if not port_hist.empty:
    st.markdown("### 📈 Portfolio Value Over Time")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=port_hist["time"],
        y=port_hist["balance"],
        mode="lines",
        name="Balance",
        line=dict(color="#00ff88", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=port_hist["time"],
        y=port_hist["realized_pnl"],
        mode="lines",
        name="Realized PnL",
        line=dict(color="#388bfd", width=1, dash="dash"),
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=250,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h"),
        yaxis_title="USD",
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Open positions ────────────────────────────────────────────────────────────

st.markdown("### 📂 Open Positions")
if open_trades.empty:
    st.info("No open positions.")
else:
    cols = ["ID", "Strategy", "Question", "Outcome", "Entry Price", "Shares", "Cost $", "Opened"]
    st.dataframe(open_trades[cols], use_container_width=True, hide_index=True, height=250)

# ── Closed trades ─────────────────────────────────────────────────────────────

st.markdown("### ✅ Closed Trades")
if closed_trades.empty:
    st.info("No closed trades yet.")
else:
    display = closed_trades.copy()
    display["PnL Color"] = display["Realized PnL"].apply(lambda x: "🟢" if (x or 0) > 0 else "🔴")
    cols = ["ID", "PnL Color", "Strategy", "Question", "Entry Price", "Exit Price", "Realized PnL", "Opened", "Closed"]
    st.dataframe(display[cols], use_container_width=True, hide_index=True, height=300)

# ── Strategy breakdown ────────────────────────────────────────────────────────

if not df.empty:
    st.markdown("### 📊 PnL by Strategy")
    strat_df = df.groupby("Strategy").agg(
        trades=("ID", "count"),
        total_cost=("Cost $", "sum"),
        realized=("Realized PnL", "sum"),
    ).reset_index()
    st.dataframe(strat_df, use_container_width=True, hide_index=True)
