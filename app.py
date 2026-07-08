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

# --- 2. DATA FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_games_by_date(date_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher"
    try:
        response = requests.get(url).json()
        games_list = response.get('dates', [{}])[0].get('games', [])
        return [{"game_id": g['gamePk'], "away": g['teams']['away']['team']['name'], "home": g['teams']['home']['team']['name'], "away_pitcher": g['teams']['away'].get('probablePitcher', {}).get('fullName', 'TBD'), "home_pitcher": g['teams']['home'].get('probablePitcher', {}).get('fullName', 'TBD')} for g in games_list]
    except: return []

@st.cache_data(ttl=3600)
def get_live_team_roster(team_name):
    return [{"name": "Sample Batter", "hand": "RHB"}] # Placeholder for your actual roster logic

@st.cache_data(ttl=7200)
def load_real_batter_stats():
    return pd.DataFrame() # Placeholder for your actual stats logic

def highlight_slam(row):
    styles = ['background-color: #121212; color: #E0E0E0;'] * len(row)
    try:
        if float(row['💥 SLAM Index']) >= 65.0: styles = ['background-color: #003366; color: #FFFFFF; font-weight: bold;'] * len(row)
    except: pass
    return styles

# --- 3. MAIN APP ---
with st.sidebar:
    st.markdown("## 📅 Matchup Slate")
    games = get_games_by_date(datetime.today().strftime('%Y-%m-%d'))
    if games:
        idx = st.selectbox("Select Matchup:", range(len(games)), format_func=lambda x: f"{games[x]['away']} @ {games[x]['home']}")
        chosen_game = games[idx]
        pitcher = st.radio("Target Pitcher:", [chosen_game['away_pitcher'], chosen_game['home_pitcher']])
    else: pitcher = None

if pitcher and pitcher != "TBD":
    st.write(f"## 📋 Pro-Report: {pitcher}")
    st.columns(4)[0].metric("SLAM Index", "66.0")
    st.markdown("---")

    try:
        # --- YOUR REAL DATA PROCESSING ---
        live_batters = get_live_team_roster(opposing_team) # 'opposing_team' is defined earlier in your script
        real_stats_df = load_real_batter_stats()
        processed_rows = []

        for b in live_batters:
            b_name_clean = b['name'].lower().replace('.', '').replace(',', '').replace("'", "")
            match = real_stats_df[real_stats_df['Name_Clean'] == b_name_clean] if not real_stats_df.empty else pd.DataFrame()
            
            if not match.empty:
                # Extract real stats
                bbe = int(match['AB'].iloc[0])
                brl = float(match['Barrel%'].iloc[0])
                hh = float(match['HardHit%'].iloc[0])
                gb = float(match['GB%'].iloc[0])
                pull_air = float(match['FB%'].iloc[0])
            else:
                # Fallback to random if no stats found
                bbe, brl, hh, gb, pull_air = 50, 8.0, 40.0, 42.0, 20.0

            # Calculate the S.L.A.M. Index
            slam_index = min(100.0, max(5.0, (brl * 3.5) + (hh * 0.5) + (pull_air * 0.3) - (gb * 0.2)))
            
            processed_rows.append({
                "Batter Name": b['name'], "Hand": b['hand'], "BBE": bbe, 
                "💥 SLAM Index": round(slam_index, 1), "Brl %": brl, "HH %": hh, "GB %": gb
            })

        # Render the final data
        df_lineup = pd.DataFrame(processed_rows).set_index("Batter Name")
        st.dataframe(df_lineup.style.apply(highlight_slam, axis=1), use_container_width=True)
