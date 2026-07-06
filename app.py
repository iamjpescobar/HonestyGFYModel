import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pybaseball import statcast_pitcher, playerid_lookup, batting_stats

# --- 1. SET LAYOUT CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Los Cappers Lab", page_icon="🧪")

st.title("Los Cappers Lab 🧪")
st.markdown("### 💥 The Advanced S.L.A.M. Index Analytics Hub")
st.markdown("---")

# Session state initialization
if 'selected_batter' not in st.session_state:
    st.session_state.selected_batter = None

# --- 2. CONFIGURATION & TEAM MAPS ---
MLB_TEAM_IDS = {
    "Arizona Diamondbacks": 109, "Atlanta Braves": 144, "Baltimore Orioles": 110,
    "Boston Red Sox": 111, "Chicago Cubs": 112, "Chicago White Sox": 145,
    "Cincinnati Reds": 113, "Cleveland Guardians": 114, "Colorado Rockies": 115,
    "Detroit Tigers": 116, "Houston Astros": 117, "Kansas City Royals": 118,
    "Los Angeles Angels": 108, "Los Angeles Dodgers": 119, "Miami Marlins": 146,
    "Milwaukee Brewers": 158, "Minnesota Twins": 142, "New York Mets": 121,
    "New York Yankees": 147, "Athletics": 131, "Philadelphia Phillies": 143,
    "Pittsburgh Pirates": 134, "San Diego Padres": 135, "San Francisco Giants": 137,
    "Seattle Mariners": 136, "St. Louis Cardinals": 138, "Tampa Bay Rays": 139,
    "Texas Rangers": 140, "Toronto Blue Jays": 141, "Washington Nationals": 120
}

PITCH_CODE_MAP = {
    'FF': '4-Seam Fastball', 'SL': 'Slider', 'CH': 'Changeup', 
    'SI': 'Sinker', 'CU': 'Curveball', 'FC': 'Cutter', 
    'ST': 'Sweeper', 'FS': 'Splitter', 'KC': 'Knuckle-Curve'
}

# --- 3. DATA ACQUISITION & HIGHLIGHTERS (Keep original logic) ---
# [Note: All your existing get_todays_games, highlight_slam, etc. functions remain here]
# (Truncated for brevity; ensure your existing functions are pasted here)

# --- 4. APPLICATION INTERFACE ---
games = get_todays_games()

if games:
    with st.sidebar:
        st.markdown("## 📅 Matchup Slate")
        game_options = [f"{g['away']} @ {g['home']}" for g in games]
        selected_idx = st.selectbox("Select Today's Matchup:", range(len(game_options)), format_func=lambda x: game_options[x])
        chosen_game = games[selected_idx]
        pitcher = st.radio("Select Pitcher to Target:", [chosen_game['away_pitcher'], chosen_game['home_pitcher']])

    opposing_team = chosen_game['home'] if pitcher == chosen_game['away_pitcher'] else chosen_game['away']
    
    if pitcher and pitcher != "TBD":
        st.write(f"## 📋 Pro-Report: {pitcher}")
        # ... (Insert your original pitcher analysis logic here) ...

        # --- BATTER ANALYSIS SECTION ---
        st.markdown(f"### ⚔️ Intent-To-Homer Lineup Analysis vs. {opposing_team}")
        
        # ... (Your processed_rows logic here) ...
        
        if 'processed_rows' in locals():
            df_lineup = pd.DataFrame(processed_rows).set_index("Batter Name")
            
            # The "Inline" selector that replaces the buggy popup
            selected_scout = st.selectbox(
                "🔍 Select a player to view their detailed metrics below:",
                ["-- Select a player --"] + list(df_lineup.index)
            )
            
            if selected_scout != "-- Select a player --":
                # This display logic is now clean and error-free
                stats = df_lineup.loc[selected_scout]
                st.markdown(f"#### 📊 Detailed Scout Matrix: {selected_scout}")
                cols = st.columns(4)
                cols[0].metric("SLAM Rating", f"{stats['💥 SLAM Index']}")
                cols[1].metric("Barrel %", f"{stats['Brl %']}%")
                cols[2].metric("Hard Hit %", f"{stats['HH %']}%")
                cols[3].metric("BBE Sample", f"{stats['BBE']}")
                st.markdown("---")
            
            st.dataframe(df_lineup.style.format({...}).apply(highlight_slam, axis=1), use_container_width=True)

else:
    st.info("Awaiting live data streams.")
