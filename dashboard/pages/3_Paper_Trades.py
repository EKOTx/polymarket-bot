"""
Paper Trades — positions, PnL, and strategy performance.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db import get_session
from traders.position_manager import get_performance_stats
from sqlalchemy import text

st.set_page_config(
    page_title="Paper Trades | Polymarket Bot",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Paper Trades")


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=10)
def load_trades():
    with get_session() as s:
        rows = s.execute(text("""
            SELECT id, market_id, question, outcome, strategy,
                   entry_price, exit_price, size_shares, cost_usd,
                   realized_pnl, unrealized_pnl, status, resolution,
                   opened_at, closed_at
            FROM paper_trades
            ORDER BY opened_at DESC
        """)).fetchall()
    cols = ["id","market_id","question","outcome","strategy",
            "entry_price","exit_price","size_shares","cost_usd",
            "realized_pnl","unrealized_pnl","status","resolution",
            "opened_at","closed_at"]
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


@st.cache_data(ttl=10)
def load_portfolio_history():
    with get_session() as s:
        rows = s.execute(text("""
            SELECT timestamp, balance, realized_pnl, unrealized_pnl,
                   total_invested, open_positions
            FROM portfolio
            ORDER BY timestamp ASC
        """)).fetchall()
    cols = ["timestamp","balance","realized_pnl","unrealized_pnl",
            "total_invested","open_positions"]
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


@st.cache_data(ttl=10)
def load_stats():
    return get_performance_stats()


df = load_trades()
port = load_portfolio_history()
stats = load_stats()

# ── KPI row ───────────────────────────────────────────────────────────────────

open_df   = df[df["status"] == "OPEN"]  if not df.empty else pd.DataFrame()
closed_df = df[df["status"] == "CLOSED"] if not df.empty else pd.DataFrame()

total_unrealized = open_df["unrealized_pnl"].sum() if not open_df.empty else 0.0
total_realized   = closed_df["realized_pnl"].sum() if not closed_df.empty else 0.0
total_pnl        = total_realized + total_unrealized

current_balance = port["balance"].iloc[-1] if not port.empty else 10000.0
win_rate = stats.get("win_rate", 0) if isinstance(stats, dict) and "win_rate" in stats else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Balance",        f"${current_balance:,.2f}",
            delta=f"{current_balance - 10000:+,.2f}")
col2.metric("Total PnL",      f"${total_pnl:+,.2f}")
col3.metric("Realized",       f"${total_realized:+,.2f}")
col4.metric("Unrealized",     f"${total_unrealized:+,.2f}")
col5.metric("Open Positions", len(open_df))
col6.metric("Win Rate",       f"{win_rate:.0%}",
            delta=f"{stats.get('total_closed', 0)} closed" if isinstance(stats, dict) else "")

st.divider()

# ── Portfolio balance chart ───────────────────────────────────────────────────

if not port.empty:
    st.subheader("💰 Portfolio Balance Over Time")
    port["timestamp"] = pd.to_datetime(port["timestamp"])
    port["total_pnl"] = port["realized_pnl"] + port["unrealized_pnl"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=port["timestamp"], y=port["balance"],
        name="Balance", line=dict(color="#00ff88", width=2),
        fill="tozeroy", fillcolor="rgba(0,255,136,0.05)",
    ))
    fig.add_trace(go.Scatter(
        x=port["timestamp"], y=port["total_pnl"],
        name="Total PnL", line=dict(color="#f77f00", width=1.5, dash="dot"),
    ))
    fig.add_hline(y=10000, line_dash="dash", line_color="#555",
                  annotation_text="Starting $10,000")
    fig.update_layout(
        paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
        font_color="#e6edf3", height=280,
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Performance stats ─────────────────────────────────────────────────────────

if isinstance(stats, dict) and "total_closed" in stats:
    st.subheader("📈 Strategy Performance")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profit Factor", f"{stats.get('profit_factor', 0):.2f}")
    c2.metric("Avg Win",       f"${stats.get('avg_win', 0):.2f}")
    c3.metric("Avg Loss",      f"${stats.get('avg_loss', 0):.2f}")
    c4.metric("Sharpe (ann.)", f"{stats.get('sharpe') or '—'}")

    by_strat = stats.get("by_strategy", {})
    if by_strat:
        strat_rows = []
        for name, d in by_strat.items():
            short = name.split(".")[-1]
            strat_rows.append({
                "Strategy":  short,
                "Trades":    d["trades"],
                "Wins":      d["wins"],
                "Win Rate":  f"{d['win_rate']:.0%}",
                "Total PnL": f"${d['pnl']:+.2f}",
                "ROI":       f"{d['roi_pct']:+.1f}%",
            })
        st.dataframe(
            pd.DataFrame(strat_rows),
            use_container_width=True, hide_index=True,
        )

    if not closed_df.empty:
        fig2 = px.histogram(
            closed_df, x="realized_pnl", nbins=20,
            color_discrete_sequence=["#00b4d8"],
            title="Realized PnL Distribution",
            labels={"realized_pnl": "Realized PnL ($)"},
        )
        fig2.add_vline(x=0, line_color="#ff4444", line_dash="dash")
        fig2.update_layout(
            paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
            font_color="#e6edf3", height=220,
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No closed trades yet — stats appear once markets resolve.")

st.divider()

# ── Open positions ────────────────────────────────────────────────────────────

st.subheader(f"🟢 Open Positions ({len(open_df)})")

if open_df.empty:
    st.info("No open positions.")
else:
    disp = open_df.copy()
    disp["strategy"] = disp["strategy"].str.split(".").str[-1]
    disp["Unrealized PnL"] = disp["unrealized_pnl"].apply(
        lambda x: f"{'🟢' if (x or 0) >= 0 else '🔴'} ${(x or 0):+.2f}"
    )
    disp["Entry"] = disp["entry_price"].map(lambda x: f"{x:.3f}")
    disp["Size"]  = disp["cost_usd"].map(lambda x: f"${x:.0f}")
    disp["Age"]   = pd.to_datetime(disp["opened_at"]).apply(
        lambda t: f"{int((pd.Timestamp.utcnow() - t.tz_localize(None)).total_seconds() // 60)}m"
        if pd.notna(t) else "—"
    )
    st.dataframe(
        disp[["question","strategy","Entry","Size","Unrealized PnL","Age"]].rename(
            columns={"question": "Market", "strategy": "Strategy"}
        ),
        use_container_width=True, hide_index=True,
    )

st.divider()

# ── Closed trades ─────────────────────────────────────────────────────────────

st.subheader(f"⚫ Closed Trades ({len(closed_df)})")

if closed_df.empty:
    st.info("No closed trades yet.")
else:
    disp2 = closed_df.copy()
    disp2["strategy"] = disp2["strategy"].str.split(".").str[-1]
    disp2["Result"] = disp2.apply(
        lambda r: (
            f"{'✅' if (r['realized_pnl'] or 0) > 0 else '❌'} "
            f"${(r['realized_pnl'] or 0):+.2f} ({r['resolution'] or '?'})"
        ), axis=1
    )
    disp2["Entry"] = disp2["entry_price"].map(lambda x: f"{x:.3f}")
    disp2["Exit"]  = disp2["exit_price"].map(
        lambda x: f"{x:.3f}" if pd.notna(x) else "—"
    )
    disp2["Cost"]  = disp2["cost_usd"].map(lambda x: f"${x:.0f}")
    st.dataframe(
        disp2[["question","strategy","Entry","Exit","Cost","Result","closed_at"]].rename(
            columns={"question": "Market", "strategy": "Strategy", "closed_at": "Closed"}
        ),
        use_container_width=True, hide_index=True,
    )

# ── Auto-refresh ──────────────────────────────────────────────────────────────

import time
if st.sidebar.checkbox("Auto-refresh (10s)", value=True):
    time.sleep(10)
    st.cache_data.clear()
    st.rerun()
