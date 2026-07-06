import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")

st.title("Los Cappers Lab 🧪")
st.markdown("### 💥 The Advanced S.L.A.M. Index Analytics Hub")
st.markdown("---")

# --- CONFIG ---
MLB_TEAM_IDS = {
    "Philadelphia Phillies": 143, "Kansas City Royals": 118, 
    "New York Yankees": 147, "Tampa Bay Rays": 139
}

@st.cache_data(ttl=60)
def get_todays_games():
    # Keep it simple: Hardcoded list for reliability while we test
    return [
        {"away": "Philadelphia Phillies", "home": "Kansas City Royals", "away_pitcher": "Cristopher Sanchez", "home_pitcher": "Noah Cameron"},
        {"away": "New York Yankees", "home": "Tampa Bay Rays", "away_pitcher": "Cam Schlittler", "home_pitcher": "Griffin Jax"}
    ]

# --- RENDER ---
games = get_todays_games()
game_options = [f"{g['away']} vs {g['home']}" for g in games]
selected_idx = st.selectbox("Select Matchup:", range(len(game_options)), format_func=lambda x: game_options[x])
chosen_game = games[selected_idx]

pitcher = st.radio("Target Pitcher:", [chosen_game['away_pitcher'], chosen_game['home_pitcher']])
opp_team = chosen_game['home'] if pitcher == chosen_game['away_pitcher'] else chosen_game['away']

if st.button("Generate Analysis"):
    st.write(f"### 📋 Report: {pitcher} vs {opp_team}")
    
    # Mock data to ensure display works
    data = []
    for i in range(5):
        data.append({"Batter": f"Batter {i+1}", "💥 SLAM Index": np.random.uniform(50, 95), "BBE": np.random.randint(20, 150)})
    
    df = pd.DataFrame(data).set_index("Batter")
    st.dataframe(df, use_container_width=True)
    st.success("Data generated successfully.")
