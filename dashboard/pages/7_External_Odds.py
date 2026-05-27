"""
External Odds — cross-platform comparison.

Shows Kalshi and PredictIt prices alongside Polymarket prices.
Highlights VALUE opportunities where PM diverges from external fair value.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db import get_session
from database.models import ExternalOddsSnapshot, Opportunity

st.set_page_config(
    page_title="External Odds | Polymarket Bot",
    page_icon="🌐",
    layout="wide",
)

st.title("🌐 External Odds — Cross-Platform Comparison")

# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_latest_external_odds():
    """Load most recent external odds snapshot per market."""
    with get_session() as session:
        # Get latest scan_id that has external odds
        from sqlalchemy import func, text
        result = session.execute(
            text("SELECT MAX(scan_id) FROM external_odds_snapshots")
        ).scalar()
        if not result:
            return pd.DataFrame()

        rows = session.execute(
            text("""
                SELECT platform, platform_market_id, title, outcome_label,
                       yes_ask, yes_bid, mid, fair_probability, volume,
                       group_id, timestamp
                FROM external_odds_snapshots
                WHERE scan_id = :sid
                ORDER BY platform, mid DESC
            """),
            {"sid": result}
        ).fetchall()

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows, columns=[
            "platform", "market_id", "title", "outcome",
            "yes_ask", "yes_bid", "mid", "fair_prob", "volume",
            "group_id", "timestamp"
        ])


@st.cache_data(ttl=30)
def load_value_opportunities():
    """Load recent VALUE-type opportunities from DB."""
    with get_session() as session:
        from sqlalchemy import text
        rows = session.execute(
            text("""
                SELECT title, edge_pct, confidence, yes_ask, yes_bid,
                       liquidity, details, timestamp
                FROM opportunities
                WHERE opportunity_type = 'OpportunityType.VALUE'
                ORDER BY timestamp DESC
                LIMIT 50
            """)
        ).fetchall()

        if not rows:
            return pd.DataFrame()

        import json
        records = []
        for r in rows:
            try:
                details = json.loads(r[6]) if r[6] else {}
            except Exception:
                details = {}
            records.append({
                "title": r[0],
                "edge_pct": r[1],
                "confidence": r[2],
                "pm_ask": r[3],
                "pm_bid": r[4],
                "liquidity": r[5],
                "external_platform": details.get("external_platform", ""),
                "external_fair": details.get("fair_prob", ""),
                "match_similarity": details.get("match_similarity", ""),
                "external_title": details.get("external_title", ""),
                "timestamp": r[7],
            })
        return pd.DataFrame(records)


@st.cache_data(ttl=30)
def load_platform_counts():
    """Count of external odds by platform in latest snapshot."""
    with get_session() as session:
        from sqlalchemy import text
        rows = session.execute(
            text("""
                SELECT platform, COUNT(*) as cnt
                FROM external_odds_snapshots
                WHERE scan_id = (SELECT MAX(scan_id) FROM external_odds_snapshots)
                GROUP BY platform
            """)
        ).fetchall()
        return {r[0]: r[1] for r in rows}


# ── Main UI ───────────────────────────────────────────────────────────────────

df_ext = load_latest_external_odds()
df_val = load_value_opportunities()
counts = load_platform_counts()

# KPI row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Kalshi Markets", counts.get("kalshi", 0))
col2.metric("PredictIt Contracts", counts.get("predictit", 0))
col3.metric("Value Signals", len(df_val))
col4.metric(
    "Top Edge",
    f"{df_val['edge_pct'].max():.1f}%" if len(df_val) > 0 else "—"
)

st.divider()

# ── Value Signals ─────────────────────────────────────────────────────────────

st.subheader("📈 Cross-Platform Value Signals")
st.caption("Where Polymarket price diverges from external fair value (edge ≥ 1.5%)")

if df_val.empty:
    st.info("No VALUE signals yet. External odds are fetched every 3rd scan cycle.")
else:
    # Format display
    disp = df_val.copy()
    disp["edge_pct"] = disp["edge_pct"].map(lambda x: f"{x:.2f}%")
    disp["confidence"] = disp["confidence"].map(lambda x: f"{x:.2f}")
    disp["pm_ask"] = disp["pm_ask"].map(lambda x: f"${x:.3f}" if pd.notna(x) else "—")
    disp["external_fair"] = disp["external_fair"].map(lambda x: f"{float(x):.3f}" if x != "" else "—")
    disp["match_similarity"] = disp["match_similarity"].map(lambda x: f"{float(x):.0%}" if x != "" else "—")

    st.dataframe(
        disp[[
            "title", "edge_pct", "confidence", "pm_ask", "external_fair",
            "external_platform", "match_similarity", "liquidity"
        ]].rename(columns={
            "title": "Market",
            "edge_pct": "Edge %",
            "confidence": "Confidence",
            "pm_ask": "PM Ask",
            "external_fair": "External Fair",
            "external_platform": "Platform",
            "match_similarity": "Match %",
            "liquidity": "Liquidity ($)",
        }),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ── External Markets Browser ──────────────────────────────────────────────────

st.subheader("🔍 External Market Browser")

if df_ext.empty:
    st.warning("No external odds loaded yet. Start the scanner to fetch Kalshi/PredictIt data.")
else:
    # Platform filter
    platforms = ["All"] + sorted(df_ext["platform"].unique().tolist())
    sel_platform = st.selectbox("Platform", platforms)

    # Search
    search = st.text_input("Search market title", placeholder="e.g. pope, president, senate")

    filtered = df_ext.copy()
    if sel_platform != "All":
        filtered = filtered[filtered["platform"] == sel_platform]
    if search:
        filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]

    # Sort by fair_prob descending
    filtered = filtered.sort_values("fair_prob", ascending=False)

    st.caption(f"Showing {len(filtered):,} of {len(df_ext):,} external contracts")

    # Display
    disp2 = filtered.copy()
    for col in ["yes_ask", "yes_bid", "mid", "fair_prob"]:
        disp2[col] = disp2[col].map(lambda x: f"{x:.3f}" if pd.notna(x) else "—")

    st.dataframe(
        disp2[[
            "platform", "title", "outcome", "yes_ask", "yes_bid", "mid",
            "fair_prob", "volume"
        ]].rename(columns={
            "platform": "Platform",
            "title": "Market",
            "outcome": "Outcome",
            "yes_ask": "Ask",
            "yes_bid": "Bid",
            "mid": "Mid",
            "fair_prob": "Fair Prob",
            "volume": "Volume",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ── Platform mid distribution ─────────────────────────────────────────────
    st.subheader("📊 Price Distribution by Platform")

    plot_df = df_ext[df_ext["mid"].notna() & (df_ext["mid"] > 0.01) & (df_ext["mid"] < 0.99)]
    if not plot_df.empty:
        fig = px.histogram(
            plot_df,
            x="mid",
            color="platform",
            nbins=40,
            barmode="overlay",
            opacity=0.7,
            title="External Market Mid Prices",
            labels={"mid": "Mid Price", "count": "Markets"},
            color_discrete_map={"kalshi": "#00b4d8", "predictit": "#f77f00"},
        )
        fig.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#161b22",
            font_color="#e6edf3",
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────

import time
if st.sidebar.checkbox("Auto-refresh (30s)", value=False):
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
