"""Opportunities page — full table with filters."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from database.db import init_db, get_session
from database.models import Opportunity as DBOpportunity

st.set_page_config(page_title="Opportunities | Polymarket Quant", layout="wide", page_icon="🎯")
init_db()


@st.cache_data(ttl=10)
def load_opps(hours: int, min_edge: float, min_conf: float) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    with get_session() as s:
        rows = (
            s.query(DBOpportunity)
            .filter(
                DBOpportunity.timestamp >= cutoff,
                DBOpportunity.edge_pct >= min_edge,
                DBOpportunity.confidence >= min_conf,
            )
            .order_by(DBOpportunity.edge_pct.desc())
            .limit(500)
            .all()
        )
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "id": r.id,
            "Type": r.opportunity_type,
            "Title": r.title,
            "Edge %": round(r.edge_pct, 3),
            "Confidence": round(r.confidence, 3),
            "EV $": round(r.expected_value, 2),
            "YES Ask": r.yes_ask,
            "NO Ask": r.no_ask,
            "Sum Mid": round(r.sum_yes_mid, 4) if r.sum_yes_mid else None,
            "Vig %": round(r.vig_pct, 2) if r.vig_pct else None,
            "Liquidity": r.liquidity,
            "Markets": r.market_count,
            "Warnings": len(json.loads(r.warnings or "[]")),
            "Scan #": r.scan_id,
            "Time": r.timestamp,
        } for r in rows])


# ── Sidebar filters ───────────────────────────────────────────────────────────

st.sidebar.markdown("## Filters")
hours = st.sidebar.slider("Look-back (hours)", 1, 24, 2)
min_edge = st.sidebar.slider("Min edge %", 0.0, 10.0, 0.5, 0.1)
min_conf = st.sidebar.slider("Min confidence", 0.0, 1.0, 0.3, 0.05)
opp_types = st.sidebar.multiselect(
    "Opportunity types",
    ["TOURNAMENT_ARB", "TOURNAMENT_ARB_RISKY", "HIGH_VIG", "ELEVATED_VIG", "VALUE", "SPREAD"],
    default=["TOURNAMENT_ARB", "TOURNAMENT_ARB_RISKY", "HIGH_VIG", "ELEVATED_VIG", "VALUE", "SPREAD"],
)
auto_refresh = st.sidebar.toggle("Auto-refresh (10s)", True)

# ── Main ─────────────────────────────────────────────────────────────────────

st.markdown("# 🎯 Opportunities")

df = load_opps(hours, min_edge, min_conf)

if df.empty:
    st.info("No opportunities match current filters. Try widening the look-back window or lowering thresholds.")
    st.stop()

# Filter by type
if opp_types:
    df = df[df["Type"].isin(opp_types)]

if df.empty:
    st.warning("No results after type filter.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", len(df))
c2.metric("Best Edge", f"{df['Edge %'].max():.2f}%")
c3.metric("Avg Confidence", f"{df['Confidence'].mean():.0%}")
c4.metric("Clean Arb", len(df[df["Type"] == "TOURNAMENT_ARB"]))

st.markdown("---")

# ── Table ─────────────────────────────────────────────────────────────────────

TYPE_ICONS = {
    "TOURNAMENT_ARB": "🟢",
    "TOURNAMENT_ARB_RISKY": "🟡",
    "HIGH_VIG": "🔴",
    "ELEVATED_VIG": "🟠",
    "VALUE": "💎",
    "SPREAD": "📐",
    "ELEVATED_VIG": "🟠",
}
display = df.copy()
display["Type"] = display["Type"].apply(lambda t: f"{TYPE_ICONS.get(t,'⚪')} {t}")
display["Liquidity"] = display["Liquidity"].apply(lambda x: f"${x:,.0f}")
display["Confidence"] = display["Confidence"].apply(lambda x: f"{x:.0%}")
display["⚠"] = display["Warnings"].apply(lambda x: "⚠" * x if x else "")

cols_show = ["Type", "Title", "Edge %", "Confidence", "Vig %", "Sum Mid", "Liquidity", "Markets", "⚠"]
st.dataframe(
    display[cols_show],
    use_container_width=True,
    height=500,
    hide_index=True,
    column_config={
        "Edge %": st.column_config.NumberColumn(format="%.2f%%"),
        "Vig %": st.column_config.NumberColumn(format="%.2f%%"),
    },
)

# ── Detail panel ──────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 🔍 Detail View")

selected_title = st.selectbox("Select opportunity to inspect:", df["Title"].tolist())
if selected_title:
    row = df[df["Title"] == selected_title].iloc[0]
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**Type:** {row['Type']}")
        st.markdown(f"**Edge:** {row['Edge %']:.3f}%")
        st.markdown(f"**Confidence:** {row['Confidence']:.0%}")
        st.markdown(f"**EV:** ${row['EV $']:.2f}")
    with c2:
        st.markdown(f"**YES Ask:** {row['YES Ask']}")
        st.markdown(f"**NO Ask:** {row['NO Ask']}")
        st.markdown(f"**Sum Mid:** {row['Sum Mid']}")
        st.markdown(f"**Vig:** {row['Vig %']}%")
    with c3:
        st.markdown(f"**Liquidity:** ${row['Liquidity']:,.0f}")
        st.markdown(f"**Market count:** {row['Markets']}")
        st.markdown(f"**Scan #:** {row['Scan #']}")
        st.markdown(f"**Time:** {row['Time']}")

# ── Edge distribution ─────────────────────────────────────────────────────────

st.markdown("### 📊 Edge Distribution")
fig = px.histogram(
    df, x="Edge %", nbins=30, color="Type",
    color_discrete_sequence=["#00ff88", "#f0883e", "#f85149", "#388bfd", "#a371f7"],
    template="plotly_dark",
)
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=250,
    margin=dict(l=0, r=0, t=10, b=0),
)
st.plotly_chart(fig, use_container_width=True)

if auto_refresh:
    import time; time.sleep(10); st.rerun()
