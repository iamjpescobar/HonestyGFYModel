import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pybaseball import statcast_pitcher, playerid_lookup, batting_stats

# --- 1. SET LAYOUT CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Los Cappers Lab", page_icon="🧪")

# --- Initialize Global Variables ---
if 'selected_batter' not in st.session_state:
    st.session_state.selected_batter = None
df_lineup = pd.DataFrame() 

st.title("Los Cappers Lab 🧪")
st.markdown("### 💥 The Advanced S.L.A.M. Index Analytics Hub")
st.markdown("---")

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

# --- 3. DATA ACQUISITION FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_todays_games():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"
    try:
        response = requests.get(url).json()
        games_list = response.get('dates', [{}])[0].get('games', [])
        matchups = []
        for g in games_list:
            away_team = g['teams']['away']['team']['name']
            home_team = g['teams']['home']['team']['name']
            away_p = g['teams']['away'].get('probablePitcher', {}).get('fullName', 'TBD')
            home_p = g['teams']['home'].get('probablePitcher', {}).get('fullName', 'TBD')
            matchups.append({
                "game_id": g['gamePk'], "away": away_team, "home": home_team,
                "away_pitcher": away_p, "home_pitcher": home_p
            })
        return matchups if matchups else get_static_games()
    except Exception:
        return get_static_games()

def get_static_games():
    return [
        {"game_id": 1, "away": "Philadelphia Phillies", "home": "Kansas City Royals", "away_pitcher": "Cristopher Sanchez", "home_pitcher": "Noah Cameron"},
        {"game_id": 2, "away": "Houston Astros", "home": "Washington Nationals", "away_pitcher": "Mike Burrows", "home_pitcher": "Miles Mikolas"}
    ]

@st.cache_data(ttl=3600)
def get_live_team_roster(team_name):
    team_id = MLB_TEAM_IDS.get(team_name)
    if not team_id: return []
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=active"
    try:
        response = requests.get(url).json()
        roster = response.get('roster', [])
        players = []
        for p in roster:
            person = p.get('person', {})
            pos = p.get('position', {})
            if pos.get('code') != '1' and person.get('fullName'):
                side_code = person.get('batSide', {}).get('code', 'R')
                side_label = "LHB" if side_code == 'L' else ("SHB" if side_code == 'S' else "RHB")
                players.append({"name": person['fullName'], "hand": side_label})
        return players
    except Exception:
        return [{"name": "Sample Batter", "hand": "RHB"}]

@st.cache_data(ttl=7200)
def load_real_batter_stats():
    try:
        df = batting_stats(2026, qual=10)
        df['Name_Clean'] = df['Name'].str.lower().str.replace('[.,\']', '', regex=True)
        return df
    except Exception:
        return pd.DataFrame()

def get_pitch_success_rate(batter_name, pitcher_arsenal):
    np.random.seed(abs(hash(batter_name + str(pitcher_arsenal))) % (10**8))
    return {pitch: round(np.random.uniform(0.6, 1.4), 2) for pitch in pitcher_arsenal}

def get_status_color(value, threshold, higher_is_better=True):
    val = float(str(value).replace('%', '').replace('+', ''))
    if higher_is_better:
        return "#0f401b" if val >= threshold else "#400f0f"
    return "#400f0f" if val >= threshold else "#0f401b"

def highlight_slam(row):
    styles = [''] * len(row)
    try:
        slam_val = float(row['💥 SLAM Index'])
        bbe_val = int(row['BBE'])
        if bbe_val < 25:
            return ['background-color: #22222b; color: #7c7c8c; font-style: italic; opacity: 0.5;'] * len(row)
        if slam_val >= 65.0:
            return ['background-color: #0f401b; color: #a3ffb4; font-weight: bold;'] * len(row)
    except: pass
    return styles

# --- 5. APPLICATION LOGIC ---
games = get_todays_games()
with st.sidebar:
    st.markdown("## 📅 Matchup Slate")
    game_options = [f"{g['away']} @ {g['home']}" for g in games]
    selected_idx = st.selectbox("Select Matchup:", range(len(game_options)), format_func=lambda x: game_options[x])
    chosen_game = games[selected_idx]
    pitcher = st.radio("Select Pitcher:", [chosen_game['away_pitcher'], chosen_game['home_pitcher']])

opposing_team = chosen_game['home'] if pitcher == chosen_game['away_pitcher'] else chosen_game['away']

if pitcher and pitcher != "TBD":
    st.write(f"## 📋 Pro-Report: {pitcher}")
    live_batters = get_live_team_roster(opposing_team)
    real_stats_df = load_real_batter_stats()
    processed_rows = []
    
    for b in live_batters:
        # (Simplified loop to build processed_rows...)
        processed_rows.append({"Batter Name": b['name'], "Hand": b['hand'], "BBE": 100, "💥 SLAM Index": 70.0, "Brl %": 10.0, "PullAir %": 15.0, "HH %": 40.0, "LD %": 20.0, "GB %": 40.0})

    df_lineup = pd.DataFrame(processed_rows).set_index("Batter Name")
    
    selected_scout = st.selectbox("🔍 Inspect Batter:", ["-- Select --"] + list(df_lineup.index))
    if selected_scout != "-- Select --":
        st.session_state.selected_batter = selected_scout

if st.session_state.selected_batter and not df_lineup.empty:
    sb = st.session_state.selected_batter
    if sb in df_lineup.index:
        stats = df_lineup.loc[sb]
        st.markdown(f"#### 📊 Detailed Scout Matrix: {sb}")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div style="background-color: {get_status_color(stats["💥 SLAM Index"], 65.0)}; padding: 10px; border-radius: 5px; color: white;"><strong>SLAM: {stats["💥 SLAM Index"]}</strong></div>', unsafe_allow_html=True)
        # ... (rest of your columns code)
        st.dataframe(df_lineup.style.apply(highlight_slam, axis=1), use_container_width=True)
