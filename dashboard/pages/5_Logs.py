"""Live log viewer."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import time
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Logs | Polymarket Quant", layout="wide", page_icon="🪵")

LOG_FILE = os.getenv("LOG_FILE", "logs/scanner.log")

st.markdown("# 🪵 Scanner Logs")

auto_refresh = st.sidebar.toggle("Auto-refresh (5s)", True)
n_lines = st.sidebar.slider("Lines to show", 50, 500, 100)
filter_level = st.sidebar.selectbox("Filter level", ["ALL", "ERROR", "WARNING", "INFO"])

log_path = Path(LOG_FILE)

if not log_path.exists():
    st.info(f"Log file not found: `{LOG_FILE}`\nStart the scanner to generate logs.")
    st.stop()

# Read last N lines
with open(log_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

if filter_level != "ALL":
    lines = [l for l in lines if filter_level in l]

lines = lines[-n_lines:]

# Color-code by level
colored = []
for line in reversed(lines):
    line = line.strip()
    if not line:
        continue
    if "error" in line.lower():
        colored.append(f"🔴 `{line}`")
    elif "warning" in line.lower() or "warn" in line.lower():
        colored.append(f"🟡 `{line}`")
    elif "scan_complete" in line or "opportunities" in line:
        colored.append(f"🟢 `{line}`")
    else:
        colored.append(f"⚪ `{line}`")

st.markdown(f"*Showing last {len(colored)} lines from `{LOG_FILE}`*")
st.markdown("---")

log_container = st.container()
with log_container:
    for c in colored[:n_lines]:
        st.markdown(c)

if auto_refresh:
    time.sleep(5)
    st.rerun()
