import streamlit as st
import pandas as pd
import numpy as np

# KEEP THIS EXACT LAYOUT
st.set_page_config(layout="wide")

st.title("Los Cappers Lab 🧪")
st.markdown("### 💥 The Advanced S.L.A.M. Index Analytics Hub")
st.markdown("---")

# 1. MATCHUP SELECTOR
matchup = st.selectbox("Select Today's Matchup:", ["Philadelphia Phillies (Cristopher Sánchez) @ Kansas City Royals (Noah Cameron)"])
pitcher = st.radio("Select Pitcher to Target:", ["Cristopher Sánchez", "Noah Cameron"])

# 2. PRO-REPORT HEADER
st.write(f"## 📋 Pro-Report: {pitcher}")

# 3. INTENT-TO-HOMER LINEUP ANALYSIS
st.markdown("### ⚔️ Intent-To-Homer Lineup Analysis vs. Kansas City Royals")
st.caption("🌲 Emerald Glow = High Volume Verified Power + Covers Arsenal Options | 🪐 Matte Grey = Small Sample Size (<45 BBE)")

# This is the exact table format from your screenshot
data = {
    "Batter Name": ["Jac Caglianone", "Luke Maile", "Nick Loftin", "Salvador Perez", "Kameron Misner", "Michael Massey"],
    "BBE": [226, 222, 201, 175, 165, 154],
    "💥 SLAM Index": [71.8, 23.2, 26.5, 23.2, 11.5, 70.5],
    "Top 3 Matchup": ["✅ Good", "✅ Good", "Neutral", "⚠️ Cold", "Neutral", "✅ Good"],
    "Brl %": [14.8, 7.5, 14.9, 6.6, 5.6, 10.2],
    "PullAir %": [23.7, 13.4, 13.0, 22.3, 18.2, 22.0],
    "HH %": [32.2, 54.2, 44.9, 51.7, 28.2, 37.1]
}

df = pd.DataFrame(data).set_index("Batter Name")
st.dataframe(df, use_container_width=True)
