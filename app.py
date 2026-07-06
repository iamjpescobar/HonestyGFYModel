import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")

# --- 1. FUNCTIONS ---
def get_todays_games():
    return [
        {"label": "Phillies @ Royals", "ap": "Cristopher Sanchez", "hp": "Noah Cameron", "away": "Philadelphia Phillies", "home": "Kansas City Royals"},
        {"label": "Yankees @ Rays", "ap": "Cam Schlittler", "hp": "Griffin Jax", "away": "New York Yankees", "home": "Tampa Bay Rays"}
    ]

# --- 2. LAYOUT & SELECTION ---
st.title("Los Cappers Lab 🧪")
games = get_todays_games()
selected = st.selectbox("Select Matchup:", games, format_func=lambda x: x['label'])

# --- 3. THE LOGIC BLOCK (This must stay here, inside the execution flow) ---
pitcher = st.radio("Target Pitcher:", [selected['ap'], selected['hp']])

if st.button("Generate Analysis"):
    # This logic only runs when the button is clicked, preventing the NameError
    if pitcher != "TBD":
        st.write(f"### 📋 Report: {pitcher}")
        
        # Mocking the display to ensure it works
        data = {"Batter": ["Hitter 1", "Hitter 2"], "💥 SLAM Index": [88.5, 72.1]}
        df = pd.DataFrame(data).set_index("Batter")
        st.dataframe(df, use_container_width=True)
        st.success("Analysis complete.")
    else:
        st.warning("Please select a valid pitcher.")
