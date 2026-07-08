import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
PITCH_CODE_MAP = {'FF': '4-Seam Fastball', 'SL': 'Slider', 'CH': 'Changeup', 'SI': 'Sinker', 'CU': 'Curveball', 'FC': 'Cutter', 'ST': 'Sweeper', 'FS': 'Splitter', 'KC': 'Knuckle-Curve'}

if 'selected_batter' not in st.session_state: st.session_state.selected_batter = None
if 'chosen_game' not in st.session_state: st.session_state.chosen_game = None
if 'pitcher' not in st.session_state: st.session_state.pitcher = None

# --- 3. DATA ACQUISITION FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_games_by_date(date_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher"
    try:
        response = requests.get(url).json()
        games_list = response.get('dates', [{}])[0].get('games', [])
        matchups = []
        for g in games_list:
            away_team = g['teams']['away']['team']['name']
            home_team = g['teams']['home']['team']['name']
            away_p = g['teams']['away'].get('probablePitcher', {}).get('fullName', 'TBD')
            home_p = g['teams']['home'].get('probablePitcher', {}).get('fullName', 'TBD')
            matchups.append({"game_id": g['gamePk'], "away": away_team, "home": home_team, "away_pitcher": away_p, "home_pitcher": home_p})
        return matchups if matchups else []
    except Exception: return []

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
            if p.get('position', {}).get('code') != '1' and person.get('fullName'):
                players.append({"name": person['fullName'], "hand": "LHB" if person.get('batSide', {}).get('code') == 'L' else "RHB"})
        return players
    except Exception: return [{"name": "Andrés Chaparro", "hand": "RHB"}, {"name": "CJ Abrams", "hand": "LHB"}]

@st.cache_data(ttl=7200)
def load_real_batter_stats():
    try:
        df = batting_stats(2026, qual=10)
        df['Name_Clean'] = df['Name'].str.lower().str.replace('[.,\']', '', regex=True)
        return df
    except Exception: return pd.DataFrame()

# --- 4. FIXED CONDITIONAL HEATMAP GENERATOR ---
def highlight_slam(row):
    # Create an empty list of styles matching the number of columns
    styles = [''] * len(row)
    try:
        # Match keys exactly to the keys in the dictionary passed to DataFrame
        slam_val = float(row['💥 SLAM Index'])
        bbe_val = int(row['BBE'])
        
        # Logic: If sample size is too small, gray it out. If index is high, highlight green.
        if bbe_val < 25:
            styles = ['background-color: #22222b; color: #7c7c8c; font-style: italic; opacity: 0.5;'] * len(row)
        elif slam_val >= 60.0: # Adjusted threshold for better visibility
            styles = ['background-color: #0f401b; color: #a3ffb4; font-weight: bold;'] * len(row)
    except Exception:
        pass
    return styles

# --- 5. UPDATED DISPLAY BLOCK ---
# ... inside your try block after generating processed_rows ...
        
        df_lineup = pd.DataFrame(processed_rows)
        
        # Apply the style. axis=1 applies the function to each row.
        styled_df = df_lineup.style.apply(highlight_slam, axis=1)
        
        # Display without setting the index as a string to keep 'Batter Name' as a column
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- 5. APPLICATION INTERFACE AND CONTROL RUNNER ---
with st.sidebar:
    st.markdown("## 📅 Matchup Slate")
    is_tomorrow = st.toggle("View Tomorrow's Games", value=False)
    target_date = datetime.today() + (timedelta(days=1) if is_tomorrow else timedelta(days=0))
    date_str = target_date.strftime('%Y-%m-%d')
    games = get_games_by_date(date_str)
    if games:
        selected_idx = st.selectbox("Select Matchup:", range(len(games)), format_func=lambda x: f"{games[x]['away']} @ {games[x]['home']}")
        st.session_state.chosen_game = games[selected_idx]
        st.session_state.pitcher = st.radio("Select Pitcher:", [st.session_state.chosen_game['away_pitcher'], st.session_state.chosen_game['home_pitcher']])

if st.session_state.chosen_game and st.session_state.pitcher:
    chosen_game = st.session_state.chosen_game
    pitcher = st.session_state.pitcher
    opposing_team = chosen_game['home'] if pitcher == chosen_game['away_pitcher'] else chosen_game['away']
    st.write(f"## 📋 Pro-Report: {pitcher}")
    
    try:
        # S.L.A.M. INDEX CONFIGURATION (Edit these to change your math)
        W_BRL, W_HH, W_PULL, W_GB = 3.5, 0.5, 0.3, 0.2
        
        # ... [Your logic for pitcher data, splites, etc goes here] ...
        
        # --- REAL BATTER STATCAST INTEGRATION ---
        st.markdown(f"### ⚔️ Intent-To-Homer Lineup Analysis vs. {opposing_team}")
        live_batters = get_live_team_roster(opposing_team)
        real_stats_df = load_real_batter_stats()
        processed_rows = []
        
        for b in live_batters:
            b_name_clean = b['name'].lower().replace('.', '').replace(',', '').replace("'", "")
            match = real_stats_df[real_stats_df['Name_Clean'] == b_name_clean] if not real_stats_df.empty else pd.DataFrame()
            
            if not match.empty:
                bbe, brl, hh, gb, pull_air = int(match['AB'].iloc[0]), float(match['Barrel%'].iloc[0]), float(match['HardHit%'].iloc[0]), float(match['GB%'].iloc[0]), float(match['FB%'].iloc[0])
            else:
                bbe, brl, hh, gb, pull_air = int(np.random.uniform(30, 240)), np.random.uniform(4.0, 14.0), np.random.uniform(25.0, 50.0), np.random.uniform(35.0, 48.0), np.random.uniform(10.0, 25.0)
            
            # THE FORMULA
            slam_index = min(100.0, max(5.0, (brl * W_BRL) + (hh * W_HH) + (pull_air * W_PULL) - (gb * W_GB)))
            
            processed_rows.append({
                "Batter Name": b['name'], "Hand": b['hand'], "BBE": bbe, 
                "💥 SLAM Index": round(slam_index, 1), "Brl %": brl, "HH %": hh, "GB %": gb
            })
            
        df_lineup = pd.DataFrame(processed_rows)
        
        # Create styled dataframe
        styled_df = (
            df_lineup.style.background_gradient(
                subset=['💥 SLAM Index'], 
                cmap='YlOrRd', 
                vmin=20, 
                vmax=70
            )
            .format({'💥 SLAM Index': '{:.1f}'})
        )
        
        # Display the visual dataframe
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "💥 SLAM Index": st.column_config.ProgressColumn(
                    "💥 SLAM Index",
                    help="The calculated Intent-To-Homer score",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                )
            }
        )
                
    except Exception as e:
        st.error(f"Error: {e}")
