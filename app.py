import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pybaseball import statcast_pitcher, playerid_lookup, batting_stats

# --- 1. FUNCTION DEFINITIONS FIRST ---
# Defining these at the top ensures they are "in memory" before the app runs
@st.cache_data(ttl=3600)
def get_todays_games():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"
    try:
        response = requests.get(url).json()
        # ... [Rest of your logic here] ...
        return matchups
    except Exception:
        return get_static_games()

def get_static_games():
    return [
        {"game_id": 1, "away": "Philadelphia Phillies", "home": "Kansas City Royals", "away_pitcher": "Cristopher Sanchez", "home_pitcher": "Noah Cameron"}
    ]

# --- 2. CONFIGURATION & LAYOUT ---
st.set_page_config(layout="wide", page_title="Los Cappers Lab", page_icon="🧪")

# --- 3. THE CALL (Only happens after functions are defined) ---
games = get_todays_games() 

# Now the rest of your UI logic follows...
