import streamlit as st
import pandas as pd
import numpy as np

# Set page to wide for "Command Center" feel
st.set_page_config(layout="wide")

st.title("Los Cappers Lab 🧪")
st.markdown("### 💥 Advanced S.L.A.M. Index Hub")

# --- 1. MOCK DATA ENGINE (Replace this with your API calls) ---
def get_mock_lineup_data():
    return pd.DataFrame({
        "Batter": ["J. Caglianone", "L. Thomas", "S. Perez", "B. Witt Jr.", "S. Marte"],
        "💥 SLAM": [88.5, 72.1, 81.4, 92.2, 65.0],
        "BBE": [140, 65, 110, 180, 50],
        "Brl %": [12.2, 8.5, 11.0, 15.4, 7.2],
        "Whiff %": [22.2, 25.7, 22.7, 17.1, 29.9]
    }).set_index("Batter")

# --- 2. LAYOUT: PITCHER PROFILE (Top Section) ---
col_game, col_pitcher = st.columns([1, 2])
with col_game:
    game = st.selectbox("Matchup:", ["Phillies @ Royals"])
with col_pitcher:
    pitcher = st.radio("Target Pitcher:", ["Cristopher Sanchez", "Noah Cameron"], horizontal=True)

st.markdown("---")
st.markdown(f"### 📋 Pitcher Scout: {pitcher}")

# Metric Grid - Mimicking the professional rating boxes
m1, m2, m3, m4 = st.columns(4)
m1.metric("PF Rating", "48.7")
m2.metric("Avg IP", "6.4")
m3.metric("K %", "28.5%")
m4.metric("Whiff %", "32.2%")

# --- 3. LAYOUT: CONFIRMED LINEUP (Bottom Section) ---
st.markdown("### ⚔️ Confirmed Lineup & S.L.A.M. Metrics")

def style_slam_grid(df):
    # This applies the 'Green/Red' professional heatmap look
    return df.style.background_gradient(subset=["💥 SLAM"], cmap="Greens") \
             .format({"💥 SLAM": "{:.1f}", "Brl %": "{:.1f}%"})

df = get_mock_lineup_data()
st.dataframe(style_slam_grid(df), use_container_width=True)
