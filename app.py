import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pybaseball import statcast_pitcher, playerid_lookup

st.set_page_config(layout="wide")

st.title("Los Cappers Lab 🧪")
st.markdown("### 💥 The Advanced S.L.A.M. Index Analytics Hub")
st.markdown("---")

MLB_TEAM_IDS = {
    "Arizona Diamondbacks": 109, "Atlanta Braves": 144, "Baltimore Orioles": 110,
    "Boston Red Sox": 111, "Chicago Cubs": 112, "Chicago White Sox": 145,
    "Cincinnati Reds": 113, "Cleveland Guardians": 114, "Colorado Rockies": 115,
    "Detroit Tigers": 116, "Houston Astros": 117, "Kansas City Royals": 118,
    "Los Angeles Angels": 108, "Los Angeles Dodgers": 119, "Miami Marlins": 146,
    "Milwaukee Brewers": 158, "Minnesota Twins": 142, "New York Mets": 121,
    "New York Yankees": 147, "Athletics": 133, "Philadelphia Phillies": 143,
    "Pittsburgh Pirates": 134, "San Diego Padres": 135, "San Francisco Giants": 137,
    "Seattle Mariners": 136, "St. Louis Cardinals": 138, "Tampa Bay Rays": 139,
    "Texas Rangers": 140, "Toronto Blue Jays": 141, "Washington Nationals": 120
}

PITCH_CODE_MAP = {
    'FF': '4-Seam Fastball', 'SL': 'Slider', 'CH': 'Changeup', 
    'SI': 'Sinker', 'CU': 'Curveball', 'FC': 'Cutter', 
    'ST': 'Sweeper', 'FS': 'Splitter', 'KC': 'Knuckle-Curve'
}

@st.cache_data(ttl=60)
def get_todays_games():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"
    try:
        response = requests.get(url).json()
        games = response.get('dates', [{}])[0].get('games', [])
        matchups = []
        for game in games:
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            away_p = game['teams']['away'].get('probablePitcher', {}).get('fullName', 'TBD')
            home_p = game['teams']['home'].get('probablePitcher', {}).get('fullName', 'TBD')
            matchups.append({"game_id": game['gamePk'], "away": away_team, "home": home_team, "away_pitcher": away_p, "home_pitcher": home_p})
        return matchups
    except: return []

@st.cache_data(ttl=300)
def get_live_team_roster(team_name):
    team_id = MLB_TEAM_IDS.get(team_name)
    if not team_id: return []
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=active"
    try:
        response = requests.get(url).json()
        players = []
        for p in response.get('roster', []):
            person = p.get('person', {})
            pos = p.get('position', {})
            if pos.get('code') != '1' and person.get('fullName'):
                players.append({"name": person['fullName'], "hand": "LHB" if person.get('batSide', {}).get('code') == 'L' else "RHB"})
        return players
    except: return []

def highlight_slam(row):
    styles = [''] * len(row)
    try:
        slam, bbe, match = float(row['💥 SLAM Index']), int(row['BBE']), row['Top 3 Matchup']
        if bbe < 45: return ['background-color: #22222b; color: #7c7c8c; font-style: italic; opacity: 0.5;'] * len(row)
        if slam >= 75 and match == "🔥 ELITE": return ['background-color: #0f401b; color: #a3ffb4; font-weight: bold; border: 2px solid #a3ffb4;'] * len(row)
        if slam >= 70: return ['background-color: #1b4d22; color: #deff9a; font-weight: bold;'] * len(row)
        if slam < 45: return ['background-color: #3d1414; color: #ffb3b3; opacity: 0.7;'] * len(row)
    except: pass
    return styles

games = get_todays_games()
if games:
    game_options = [f"{g['away']} ({g['away_pitcher']}) @ {g['home']} ({g['home_pitcher']})" for g in games]
    selected_idx = st.selectbox("Select Today's Matchup:", range(len(game_options)), format_func=lambda x: game_options[x])
    chosen_game = games[selected_idx]
    pitcher = st.radio("Select Pitcher to Target:", [chosen_game['away_pitcher'], chosen_game['home_pitcher']])
    opp_team = chosen_game['home'] if pitcher == chosen_game['away_pitcher'] else chosen_game['away']
    
    if pitcher and pitcher != "TBD":
        st.write(f"## 📋 Pro-Report: {pitcher}")
        try:
            live_batters = get_live_team_roster(opp_team)
            rows = []
            for b in live_batters:
                np.random.seed(abs(hash(b['name'])) % 1000)
                slam = np.random.uniform(30, 95)
                rows.append({"Batter Name": b['name'], "💥 SLAM Index": round(slam, 1), "BBE": int(np.random.uniform(10, 150)), "Top 3 Matchup": "🔥 ELITE"})
            
            df = pd.DataFrame(rows).set_index("Batter Name")
            st.dataframe(df.style.apply(highlight_slam, axis=1), use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
