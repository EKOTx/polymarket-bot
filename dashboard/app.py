"""
Polymarket Quant Dashboard — Main Page (Overview)

Run: streamlit run dashboard/app.py
"""

from __future__ import annotations
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from database.db import init_db, get_session
from database.models import (
    ScanRun, Opportunity as DBOpportunity,
    PaperTrade as DBTrade, Portfolio as DBPortfolio,
    PriceSnapshot, Market as DBMarket,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Polymarket Quant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark styles ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Metric cards */
    [data-testid="metric-container"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
    }
    /* Remove default padding */
    .block-container { padding-top: 1rem; }
    /* Status badge */
    .status-live { color: #00ff88; font-weight: bold; }
    .status-stopped { color: #f85149; font-weight: bold; }
    /* Table header */
    thead tr th { background: #161b22 !important; }
    /* Scrollable table */
    .dataframe-container { max-height: 400px; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)


# ── DB helpers ────────────────────────────────────────────────────────────────

@st.cache_resource
def _init():
    init_db()
    return True

_init()


@st.cache_data(ttl=10)
def load_latest_scan() -> dict:
    with get_session() as s:
        run = s.query(ScanRun).order_by(ScanRun.id.desc()).first()
        if not run:
            return {}
        return {
            "id": run.id,
            "markets_fetched": run.markets_fetched,
            "markets_priced": run.markets_priced,
            "opportunities_found": run.opportunities_found,
            "duration_seconds": run.duration_seconds,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "error": run.error,
        }


@st.cache_data(ttl=10)
def load_opportunities(limit: int = 50, hours: int = 1) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    with get_session() as s:
        rows = (
            s.query(DBOpportunity)
            .filter(DBOpportunity.timestamp >= cutoff)
            .order_by(DBOpportunity.timestamp.desc(), DBOpportunity.edge_pct.desc())
            .limit(limit)
            .all()
        )
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "Type": r.opportunity_type,
            "Title": r.title[:55],
            "Edge %": r.edge_pct,
            "Confidence": r.confidence,
            "EV $": r.expected_value,
            "YES Ask": r.yes_ask,
            "NO Ask": r.no_ask,
            "Sum Mid": r.sum_yes_mid,
            "Vig %": r.vig_pct,
            "Liquidity $": r.liquidity,
            "Markets": r.market_count,
            "Time": r.timestamp,
        } for r in rows])


@st.cache_data(ttl=10)
def load_portfolio_history(hours: int = 24) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    with get_session() as s:
        rows = (
            s.query(DBPortfolio)
            .filter(DBPortfolio.timestamp >= cutoff)
            .order_by(DBPortfolio.timestamp)
            .all()
        )
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "time": r.timestamp,
            "balance": r.balance,
            "realized_pnl": r.realized_pnl,
            "unrealized_pnl": r.unrealized_pnl,
            "open_positions": r.open_positions,
            "total_trades": r.total_trades,
        } for r in rows])


@st.cache_data(ttl=10)
def load_scan_history(n: int = 50) -> pd.DataFrame:
    with get_session() as s:
        rows = (
            s.query(ScanRun)
            .order_by(ScanRun.id.desc())
            .limit(n)
            .all()
        )
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "ID": r.id,
            "Markets": r.markets_priced,
            "Opportunities": r.opportunities_found,
            "Duration (s)": r.duration_seconds,
            "Started": r.started_at,
            "Error": r.error or "",
        } for r in rows])


@st.cache_data(ttl=10)
def load_portfolio_current() -> dict:
    with get_session() as s:
        latest = s.query(DBPortfolio).order_by(DBPortfolio.id.desc()).first()
        if not latest:
            starting = float(os.getenv("PAPER_STARTING_BALANCE", "10000"))
            return {
                "balance": starting,
                "starting_balance": starting,
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "open_positions": 0,
                "total_trades": 0,
            }
        return {
            "balance": latest.balance,
            "starting_balance": latest.starting_balance,
            "realized_pnl": latest.realized_pnl,
            "unrealized_pnl": latest.unrealized_pnl,
            "open_positions": latest.open_positions,
            "total_trades": latest.total_trades,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _delta_color(val: float) -> str:
    return "normal" if val >= 0 else "inverse"


def _format_pct(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    return f"{val:+.2f}%"


def _type_badge(t: str) -> str:
    colors = {
        "TOURNAMENT_ARB": "🟢",
        "TOURNAMENT_ARB_RISKY": "🟡",
        "HIGH_VIG": "🔴",
        "ELEVATED_VIG": "🟠",
        "VALUE": "💎",
        "SPREAD": "📐",
    }
    return f"{colors.get(t, '⚪')} {t}"


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📊 Polymarket Quant")
    st.markdown("---")

    auto_refresh = st.toggle("Auto-refresh (10s)", value=True)

    st.markdown("### Navigation")
    st.markdown("""
- 🏠 **Dashboard** ← you are here
- 📋 [Opportunities](Opportunities)
- 🏆 [Tournament Analysis](Tournament_Analysis)
- 🧾 [Paper Trades](Paper_Trades)
- 📈 [Market Analysis](Market_Analysis)
- 🪵 [Logs](Logs)
- ⚙️ [Settings](Settings)
    """)

    st.markdown("---")

    env_mode = "🟡 PAPER" if os.getenv("DRY_RUN", "true").lower() == "true" else "🔴 LIVE"
    st.markdown(f"**Mode:** {env_mode}")

    scan = load_latest_scan()
    if scan.get("finished_at"):
        age = (datetime.utcnow() - scan["finished_at"]).seconds
        st.markdown(f"**Last scan:** {age}s ago")
    else:
        st.markdown("**Last scan:** No data yet")
        st.caption("Run `python scanner.py` to start scanning")


# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("# 📊 Polymarket Quant Dashboard")
st.markdown(f"*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*")

# ── Top KPI metrics ───────────────────────────────────────────────────────────

scan = load_latest_scan()
portfolio = load_portfolio_current()
opps_df = load_opportunities(limit=200, hours=1)

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    markets = scan.get("markets_priced", 0)
    st.metric("Markets Scanned", markets, help="Markets with real CLOB prices in last scan")

with col2:
    n_opps = len(opps_df) if not opps_df.empty else 0
    st.metric("Opportunities (1h)", n_opps)

with col3:
    balance = portfolio.get("balance", 0)
    start = portfolio.get("starting_balance", 10000)
    st.metric("Paper Balance", f"${balance:,.2f}", f"${balance - start:+,.2f}")

with col4:
    rpnl = portfolio.get("realized_pnl", 0)
    st.metric("Realized PnL", f"${rpnl:+,.2f}")

with col5:
    upnl = portfolio.get("unrealized_pnl", 0)
    st.metric("Unrealized PnL", f"${upnl:+,.2f}")

with col6:
    n_trades = portfolio.get("total_trades", 0)
    n_open = portfolio.get("open_positions", 0)
    st.metric("Trades", n_trades, f"{n_open} open")

st.markdown("---")

# ── Two-column layout ─────────────────────────────────────────────────────────

left, right = st.columns([2, 1])

# ── Opportunities table ───────────────────────────────────────────────────────

with left:
    st.markdown("### 🎯 Recent Opportunities")

    if opps_df.empty:
        st.info("No opportunities detected yet. Start `python scanner.py` to begin scanning.")
    else:
        # Style the dataframe
        display = opps_df.copy()
        display["Type"] = display["Type"].apply(_type_badge)
        display["Edge %"] = display["Edge %"].apply(lambda x: f"{x:.2f}%")
        display["Confidence"] = display["Confidence"].apply(lambda x: f"{x:.0%}")
        display["Liquidity $"] = display["Liquidity $"].apply(lambda x: f"${x:,.0f}")

        st.dataframe(
            display[["Type", "Title", "Edge %", "Confidence", "Vig %", "Liquidity $", "Markets"]],
            use_container_width=True,
            height=320,
            hide_index=True,
        )

        # Type breakdown
        st.markdown("**Breakdown by type:**")
        type_counts = opps_df["Type"].value_counts()
        fig_pie = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            color_discrete_sequence=["#00ff88", "#f0883e", "#f85149", "#388bfd", "#a371f7"],
            hole=0.4,
        )
        fig_pie.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            height=220,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(fig_pie, use_container_width=True)


# ── Scan health + portfolio chart ─────────────────────────────────────────────

with right:
    st.markdown("### 🔍 Scanner Health")

    scan_hist = load_scan_history(20)
    if scan_hist.empty:
        st.info("No scans yet.")
    else:
        # Markets per scan sparkline
        fig_spark = go.Figure()
        fig_spark.add_trace(go.Scatter(
            x=scan_hist["ID"].tolist()[::-1],
            y=scan_hist["Markets"].tolist()[::-1],
            mode="lines+markers",
            line=dict(color="#00ff88", width=2),
            marker=dict(size=4),
            name="Markets",
        ))
        fig_spark.add_trace(go.Scatter(
            x=scan_hist["ID"].tolist()[::-1],
            y=scan_hist["Opportunities"].tolist()[::-1],
            mode="lines+markers",
            line=dict(color="#f0883e", width=2),
            marker=dict(size=4),
            name="Opportunities",
            yaxis="y2",
        ))
        fig_spark.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=180,
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(title="Markets", color="#00ff88"),
            yaxis2=dict(title="Opps", overlaying="y", side="right", color="#f0883e"),
            legend=dict(orientation="h", y=-0.3),
            xaxis_title="Scan #",
        )
        st.plotly_chart(fig_spark, use_container_width=True)

        latest = scan_hist.iloc[0]
        err = latest.get("Error", "")
        status = "🔴 Error" if err else "🟢 OK"
        st.markdown(f"**Last scan status:** {status}")
        if err:
            st.error(f"Error: {err[:100]}")
        st.caption(f"Duration: {latest.get('Duration (s)', 0):.1f}s | "
                   f"Markets: {latest.get('Markets', 0)} | "
                   f"Opps: {latest.get('Opportunities', 0)}")

    st.markdown("### 💰 Portfolio PnL")
    port_hist = load_portfolio_history(24)
    if port_hist.empty:
        st.info("No portfolio history yet.")
    else:
        fig_pnl = go.Figure()
        pnl_series = port_hist["realized_pnl"] + port_hist["unrealized_pnl"]
        fig_pnl.add_trace(go.Scatter(
            x=port_hist["time"],
            y=pnl_series,
            mode="lines",
            fill="tozeroy",
            line=dict(
                color="#00ff88" if pnl_series.iloc[-1] >= 0 else "#f85149",
                width=2,
            ),
            fillcolor="rgba(0,255,136,0.1)" if pnl_series.iloc[-1] >= 0 else "rgba(248,81,73,0.1)",
        ))
        fig_pnl.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=180,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title=None,
            yaxis_title="PnL ($)",
            showlegend=False,
        )
        st.plotly_chart(fig_pnl, use_container_width=True)


# ── Recent scan log ───────────────────────────────────────────────────────────

with st.expander("📋 Recent Scan Runs", expanded=False):
    scan_hist = load_scan_history(10)
    if not scan_hist.empty:
        st.dataframe(scan_hist, use_container_width=True, hide_index=True)
    else:
        st.info("No scan history.")


# ── Auto-refresh ──────────────────────────────────────────────────────────────

if auto_refresh:
    time.sleep(10)
    st.rerun()
