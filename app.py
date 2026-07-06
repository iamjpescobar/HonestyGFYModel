import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pybaseball import statcast_pitcher, playerid_lookup, batting_stats

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Los Cappers Lab", page_icon="🧪")

MLB_TEAM_IDS = {
    "Philadelphia Phillies": 143, "Kansas City Royals": 118, 
    "Houston Astros": 117, "Washington Nationals": 120
}

PITCH_CODE_MAP = {'FF': '4-Seam Fastball', 'SL': 'Slider', 'CH': 'Changeup', 'SI': 'Sinker', 'CU': 'Curveball'}

if 'selected_batter' not in st.session_state:
    st.session_state.selected_batter = None

# --- 2. HELPER FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_todays_games():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"
    try:
        response = requests.get(url).json()
        games_list = response.get('dates', [{}])[0].get('games', [])
        return [{"game_id": g['gamePk'], "away": g['teams']['away']['team']['name'], 
                 "home": g['teams']['home']['team']['name'], 
                 "away_pitcher": g['teams']['away'].get('probablePitcher', {}).get('fullName', 'TBD'),
                 "home_pitcher": g['teams']['home'].get('probablePitcher', {}).get('fullName', 'TBD')} 
                for g in games_list]
    except:
        return [{"game_id": 1, "away": "Philadelphia Phillies", "home": "Kansas City Royals", "away_pitcher": "Cristopher Sanchez", "home_pitcher": "Noah Cameron"}]

def highlight_pitcher_matrix(df):
    style_df = pd.DataFrame('', index=df.index, columns=df.columns)
    for col in df.columns:
        for idx in df.index:
            try:
                val = float(str(df.loc[idx, col]).replace('%', ''))
                if col in ['ERA', 'xERA'] and val >= 3.8: style_df.loc[idx, col] = 'background-color: #5c1414; color: #ffb3b3;'
                elif col in ['ERA', 'xERA'] and val <= 2.8: style_df.loc[idx, col] = 'background-color: #0f401b; color: #a3ffb4;'
            except: pass
    return style_df

# --- 3. MAIN APP INTERFACE ---
st.title("Los Cappers Lab 🧪")
games = get_todays_games()

if games:
    game_list = [f"{g['away']} @ {g['home']}" for g in games]
    selected = st.sidebar.selectbox("Select Matchup", range(len(game_list)), format_func=lambda x: game_list[x])
    chosen_game = games[selected]
    
    pitcher = st.sidebar.radio("Select Pitcher", [chosen_game['away_pitcher'], chosen_game['home_pitcher']])
    
    if pitcher != "TBD":
        st.write(f"## 📋 Pro-Report: {pitcher}")
        # Build dummy matrix for demonstration
        data = {"ERA": [3.40, 2.14, 3.84], "xERA": [3.32, 2.15, 3.76]}
        df = pd.DataFrame(data, index=["Season", "vs LHB", "vs RHB"])
        
        st.dataframe(df.style.apply(highlight_pitcher_matrix, axis=None))
else:
    st.info("Awaiting live data streams.")
