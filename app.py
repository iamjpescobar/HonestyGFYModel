import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pybaseball import batting_stats

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Los Cappers Lab", page_icon="🧪")
st.title("Los Cappers Lab 🧪")
st.markdown("---")

# --- 2. DATA FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_todays_games():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"
    try:
        response = requests.get(url).json()
        games_list = response.get('dates', [{}])[0].get('games', [])
        matchups = []
        for g in games_list:
            matchups.append({
                "away": g['teams']['away']['team']['name'],
                "home": g['teams']['home']['team']['name'],
                "away_p": g['teams']['away'].get('probablePitcher', {}).get('fullName', 'TBD'),
                "home_p": g['teams']['home'].get('probablePitcher', {}).get('fullName', 'TBD')
            })
        return matchups
    except:
        return []

# --- 3. UI GENERATOR ---
games = get_todays_games()

if games:
    tabs = st.tabs([f"{g['away']} @ {g['home']}" for g in games])
    
    for i, tab in enumerate(tabs):
        with tab:
            game = games[i]
            st.subheader(f"Pro-Report: {game['away_p']} vs {game['home_p']}")
            
            # Simple selector to initiate data load
            target_pitcher = st.radio("Select Pitcher:", [game['away_p'], game['home_p']], key=f"p_{i}")
            
            if target_pitcher != "TBD":
                st.info(f"Analyzing {target_pitcher} matchup data...")
                # Add your analysis logic here
else:
    st.info("Loading MLB schedule...")
