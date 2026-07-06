import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Simple setup, no complex CSS
st.set_page_config(layout="wide")
st.title("Los Cappers Lab 🧪")

# 1. Simple, Reliable Schedule Fetch
def get_simple_games():
    # Placeholder: Keeping it simple to ensure it runs
    return [
        {"label": "Phillies @ Royals", "ap": "Cristopher Sanchez", "hp": "Noah Cameron", "opp": "Kansas City Royals"},
        {"label": "Yankees @ Rays", "ap": "Cam Schlittler", "hp": "Griffin Jax", "opp": "Tampa Bay Rays"}
    ]

# 2. Main Execution Flow
games = get_simple_games()
selected = st.selectbox("Select Matchup:", games, format_func=lambda x: x['label'])

# 3. Simple Interaction
target = st.radio("Select Pitcher:", [selected['ap'], selected['hp']])

if st.button("Run Analysis"):
    st.write(f"### Analyzing {target}...")
    
    # Simple Mock Data Table to verify it loads without crashing
    data = {
        "Batter": ["Hitter A", "Hitter B", "Hitter C"],
        "💥 SLAM Index": [85.5, 72.1, 40.2],
        "BBE": [150, 60, 20]
    }
    df = pd.DataFrame(data)
    st.dataframe(df)
else:
    st.info("Click 'Run Analysis' to generate the report.")
