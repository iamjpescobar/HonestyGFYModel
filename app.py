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

if 'selected_batter' not in st.session_state:
    st.session_state.selected_batter = None

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
            
            if away_team == "Philadelphia Phillies" and away_p == "TBD": away_p = "Cristopher Sanchez"
            if home_team == "Kansas City Royals" and home_p == "TBD": home_p = "Noah Cameron"
            if away_team == "Houston Astros" and away_p == "TBD": away_p = "Mike Burrows"
            if home_team == "Washington Nationals" and home_p == "TBD": home_p = "Miles Mikolas"
                
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
        players = []
        for p in response.get('roster', []):
            person = p.get('person', {})
            # This line fixes the Handedness issue
            side_code = person.get('batSide', {}).get('code', 'R')
            side_label = "LHB" if side_code == 'L' else ("SHB" if side_code == 'S' else "RHB")
            
            if p.get('position', {}).get('code') != '1':
                players.append({"name": person['fullName'], "hand": side_label})
        return players
    except:
        return []
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=active"
    try:
        response = requests.get(url).json()
        roster = response.get('roster', [])
        players = []
        for p in roster:
            person = p.get('person', {})
            pos = p.get('position', {})
            if pos.get('code') != '1' and person.get('fullName'):
                players.append({
                    "name": person['fullName'],
                    "hand": "LHB" if person.get('batSide', {}).get('code') == 'L' else "RHB"
                })
        return players
    except Exception:
        if "Royals" in team_name:
            return [{"name": "Jac Caglianone", "hand": "LHB"}, {"name": "Luke Maile", "hand": "RHB"}, {"name": "Nick Loftin", "hand": "RHB"}, {"name": "Salvador Perez", "hand": "RHB"}]
        return [{"name": "Andrés Chaparro", "hand": "RHB"}, {"name": "CJ Abrams", "hand": "LHB"}, {"name": "Curtis Mead", "hand": "RHB"}]

@st.cache_data(ttl=7200)
def load_real_batter_stats():
    try:
        df = batting_stats(2026, qual=10)
        df['Name_Clean'] = df['Name'].str.lower().str.replace('[.,\']', '', regex=True)
        return df
    except Exception:
        return pd.DataFrame()
@st.cache_data(ttl=3600)
def get_batter_affinity_multiplier(batter_name, pitcher_data):
    """
    Checks the pitcher's primary pitch and returns an affinity multiplier 
    based on a simplified simulated affinity lookup.
    """
    if pitcher_data is None or pitcher_data.empty:
        return 1.0
    
    # Identify primary pitch code (most frequent)
    primary_code = pitcher_data['pitch_type'].value_counts().idxmax()
    
    # Logic: If batter is 'Elite' or 'Good', apply a 1.10 multiplier (10% boost)
    # This simulates checking the batter's historical wOBA vs that pitch type
    # In a production app, replace with a real lookup: batting_stats_vs_pitch(batter_id, primary_code)
    np.random.seed(abs(hash(batter_name)) % (10**8))
    # Randomly assign affinity based on a 40% success rate
    return 1.10 if np.random.rand() > 0.6 else 1.0
# --- 4. CONDITIONAL HEATMAP GENERATOR ---
def highlight_slam(row):
    styles = [''] * len(row)
    try:
        slam_val = float(row['💥 SLAM Index'])
        brl_val = float(row['Brl %'])
        hh_val = float(row['HH %'])
        gb_val = float(row['GB %'])
        bbe_val = int(row['BBE'])
        
        if bbe_val < 25:
            for i in range(len(row)):
                styles[i] = 'background-color: #22222b; color: #7c7c8c; font-style: italic; opacity: 0.5;'
            return styles
            
        if slam_val >= 65.0 and brl_val >= 10.0 and hh_val >= 35.0 and gb_val <= 42.0:
            for i in range(len(row)):
                styles[i] = 'background-color: #0f401b; color: #a3ffb4; font-weight: bold;'
    except:
        pass
    return styles

# --- 5. APPLICATION INTERFACE AND CONTROL RUNNER ---
games = get_todays_games()

if games:
    with st.sidebar:
        st.markdown("## 📅 Matchup Slate")
        game_options = [f"{g['away']} @ {g['home']}" for g in games]
        selected_idx = st.selectbox("Select Today's Matchup:", range(len(game_options)), format_func=lambda x: game_options[x])
        chosen_game = games[selected_idx]
        st.markdown("---")
        pitcher = st.radio("Select Pitcher to Target:", [chosen_game['away_pitcher'], chosen_game['home_pitcher']])
    
    opposing_team = chosen_game['home'] if pitcher == chosen_game['away_pitcher'] else chosen_game['away']
    
    if pitcher and pitcher != "TBD":
        st.write(f"## 📋 Pro-Report: {pitcher}")
        
        # PITCHER PROCESSING BLOCK
        try:
            # ... (Keep your existing pitcher lookup and splits logic here) ...
            # Ensure all your pitcher code remains indented under this 'try'
            st.markdown("### 🔨 Advanced Statcast Sabermetric Splits")
            # ... (Rest of your pitcher stats display code) ...
        except Exception as e:
            st.error(f"Error processing pitcher data: {e}")
        
        # BATTER ANALYSIS BLOCK (Outside the Try/Except)
        st.markdown(f"### ⚔️ Intent-To-Homer Lineup Analysis vs. {opposing_team}")
        
        live_batters = get_live_team_roster(opposing_team)
        real_stats_df = load_real_batter_stats()
        
        # Safety Check for Data
        if not real_stats_df.empty and 'Name_Clean' not in real_stats_df.columns:
            real_stats_df['Name_Clean'] = real_stats_df['Name'].str.lower().str.replace('[.,\']', '', regex=True)
            
        processed_rows = []
        for b in live_batters:
            b_name_clean = b['name'].lower().replace('.', '').replace(',', '').replace("'", "")
            match = real_stats_df[real_stats_df['Name_Clean'] == b_name_clean] if not real_stats_df.empty else pd.DataFrame()
            
            # S.L.A.M Calculation
            if not match.empty:
                brl = float(match.get('Barrel%', [8.5]).iloc[0])
                hh = float(match.get('HardHit%', [40.0]).iloc[0])
                slam_index = (brl * 3.5) + (hh * 0.5)
            else:
                slam_index = 0.0 # Fallback
            
            processed_rows.append({"Batter Name": b['name'], "💥 SLAM Index": round(slam_index, 1)})

        if processed_rows:
            df_lineup = pd.DataFrame(processed_rows).set_index("Batter Name")
            st.dataframe(df_lineup.style.apply(highlight_slam, axis=1), use_container_width=True)
else:
    st.info("Awaiting live MLB schedule initialization data streams.")
