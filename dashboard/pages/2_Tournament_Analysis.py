"""Tournament Analysis — vig and group mispricing view."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from database.db import init_db, get_session
from database.models import Opportunity as DBOpportunity

st.set_page_config(page_title="Tournament | Polymarket Quant", layout="wide", page_icon="🏆")
init_db()


@st.cache_data(ttl=15)
def load_tournament_opps(hours: int = 2) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    types = ["TOURNAMENT_ARB", "TOURNAMENT_ARB_RISKY", "HIGH_VIG", "ELEVATED_VIG"]
    with get_session() as s:
        rows = (
            s.query(DBOpportunity)
            .filter(
                DBOpportunity.timestamp >= cutoff,
                DBOpportunity.opportunity_type.in_(types),
            )
            .order_by(DBOpportunity.timestamp.desc())
            .limit(200)
            .all()
        )
        if not rows:
            return pd.DataFrame()

        records = []
        for r in rows:
            det = json.loads(r.details or "{}")
            records.append({
                "Event": r.event_title[:60],
                "Type": r.opportunity_type,
                "Markets": r.market_count,
                "Sum Mid": round(r.sum_yes_mid, 4) if r.sum_yes_mid else None,
                "Sum Ask": round(det.get("sum_ask", 0), 4),
                "Buy-All Profit %": round(det.get("buy_all_profit_pct", 0), 3),
                "Vig %": round(r.vig_pct, 2) if r.vig_pct else None,
                "Field Risk %": round(det.get("field_probability", 0) * 100, 1),
                "Liquidity": r.liquidity,
                "Confidence": round(r.confidence, 3),
                "Warnings": len(json.loads(r.warnings or "[]")),
                "Scan #": r.scan_id,
                "details": det,
            })
        return pd.DataFrame(records)


# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.markdown("## Tournament Filters")
hours = st.sidebar.slider("Look-back (hours)", 1, 12, 2)
auto_refresh = st.sidebar.toggle("Auto-refresh (15s)", True)

# ── Main ─────────────────────────────────────────────────────────────────────

st.markdown("# 🏆 Tournament Analysis")
st.caption("Groups markets by event and detects vig, buy-all arb, and mispricing.")

df = load_tournament_opps(hours)

if df.empty:
    st.info("No tournament data yet. Ensure scanner is running.")
    st.stop()

# Deduplicate by event (keep latest scan)
df = df.drop_duplicates(subset=["Event", "Type"], keep="first")

# ── KPIs ─────────────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
arb = df[df["Type"] == "TOURNAMENT_ARB"]
high_vig = df[df["Vig %"].notna() & (df["Vig %"] > 5)]
c1.metric("Groups Analyzed", len(df))
c2.metric("Buy-All Arb", len(arb), help="sum_ask < 1.0 with no warnings")
c3.metric("High Vig (>5%)", len(high_vig))
c4.metric("Best Buy-All", f"{df['Buy-All Profit %'].max():.2f}%" if len(arb) else "None")

st.markdown("---")

# ── Vig bar chart ─────────────────────────────────────────────────────────────

st.markdown("### 📊 Vig by Tournament Group")

vig_df = df[df["Vig %"].notna()].sort_values("Vig %", ascending=False).head(20)

if not vig_df.empty:
    fig = go.Figure(go.Bar(
        x=vig_df["Vig %"],
        y=vig_df["Event"],
        orientation="h",
        marker=dict(
            color=vig_df["Vig %"],
            colorscale=[[0, "#388bfd"], [0.5, "#f0883e"], [1.0, "#f85149"]],
        ),
        text=[f"{v:.1f}%" for v in vig_df["Vig %"]],
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(300, len(vig_df) * 28),
        margin=dict(l=0, r=80, t=10, b=0),
        xaxis_title="Vig %",
        yaxis_title=None,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Full table ────────────────────────────────────────────────────────────────

st.markdown("### 📋 All Tournament Groups")

TYPE_ICONS = {
    "TOURNAMENT_ARB": "🟢 BUY_ALL",
    "TOURNAMENT_ARB_RISKY": "🟡 BUY_ALL_RISKY",
    "HIGH_VIG": "🔴 HIGH_VIG",
    "ELEVATED_VIG": "🟠 ELEVATED_VIG",
    "NORMAL_VIG": "⚪ NORMAL_VIG",
}
display = df.copy()
display["Type"] = display["Type"].apply(lambda t: TYPE_ICONS.get(t, t))
display["Liquidity"] = display["Liquidity"].apply(lambda x: f"${x:,.0f}")
display["⚠"] = display["Warnings"].apply(lambda x: "⚠" * x)

cols = ["Type", "Event", "Markets", "Sum Mid", "Vig %", "Buy-All Profit %", "Field Risk %", "Liquidity", "Confidence", "⚠"]
st.dataframe(
    display[cols],
    use_container_width=True,
    height=420,
    hide_index=True,
    column_config={
        "Vig %": st.column_config.NumberColumn(format="%.2f%%"),
        "Buy-All Profit %": st.column_config.NumberColumn(format="%.3f%%"),
        "Field Risk %": st.column_config.NumberColumn(format="%.1f%%"),
    },
)

# ── Detail: top market outcomes ───────────────────────────────────────────────

st.markdown("---")
st.markdown("### 🔍 Group Detail")

events = df["Event"].tolist()
if events:
    selected = st.selectbox("Select event:", events)
    row = df[df["Event"] == selected].iloc[0]
    det = row.get("details", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Markets", row["Markets"])
    c2.metric("Vig", f"{row['Vig %']:.2f}%")
    c3.metric("Buy-All Profit", f"{row['Buy-All Profit %']:.3f}%")

    if row["Warnings"] > 0:
        st.warning(f"⚠ {row['Warnings']} warning(s) — see details dict")

    top_markets = det.get("top_markets", [])
    if top_markets:
        st.markdown("**Top outcomes (YES price):**")
        tm_df = pd.DataFrame(top_markets)
        if "yes_mid" in tm_df.columns:
            tm_df["yes_mid"] = tm_df["yes_mid"].apply(lambda x: f"{x*100:.1f}%" if x else "—")
            tm_df["yes_ask"] = tm_df["yes_ask"].apply(lambda x: f"{x:.3f}" if x else "—")
            tm_df["liquidity"] = tm_df["liquidity"].apply(lambda x: f"${x:,.0f}" if x else "—")
        st.dataframe(tm_df, use_container_width=True, hide_index=True)

if auto_refresh:
    import time; time.sleep(15); st.rerun()
