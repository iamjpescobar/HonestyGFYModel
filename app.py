import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pybaseball import statcast_pitcher, playerid_lookup, batting_stats

# --- 1. SETUP ---
st.set_page_config(layout="wide", page_title="Los Cappers Lab", page_icon="🧪")
st.title("Los Cappers Lab 🧪")
st.markdown("### 💥 The Advanced S.L.A.M. Index Analytics Hub")

def highlight_slam(row):
    styles = ['background-color: #121212; color: #E0E0E0;'] * len(row)
    try:
        if float(row['💥 SLAM Index']) >= 65.0: 
            styles = ['background-color: #003366; color: #FFFFFF; font-weight: bold;'] * len(row)
    except: pass
    return styles

# --- 2. DATA ACQUISITION ---
@st.cache_data(ttl=3600)
def get_games_by_date(date_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher"
    try:
        r = requests.get(url).json()
        games = r.get('dates', [{}])[0].get('games', [])
        return [{"away": g['teams']['away']['team']['name'], "home": g['teams']['home']['team']['name'], 
                 "away_pitcher": g['teams']['away'].get('probablePitcher', {}).get('fullName', 'TBD'),
                 "home_pitcher": g['teams']['home'].get('probablePitcher', {}).get('fullName', 'TBD')} for g in games]
    except: return []

# --- 3. UI LAYOUT ---
with st.sidebar:
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
        # 1. Fetch live roster for the opposing team
        # 'opposing_team' is determined by your sidebar selection
        live_batters = get_live_team_roster(opposing_team) 
        real_stats_df = load_real_batter_stats()
        processed_rows = []

        # 2. Iterate and process each batter
        for b in live_batters:
            b_name_clean = b['name'].lower().replace('.', '').replace(',', '').replace("'", "")
            match = real_stats_df[real_stats_df['Name_Clean'] == b_name_clean] if not real_stats_df.empty else pd.DataFrame()
            
            # Logic to calculate S.L.A.M. Index
            if not match.empty:
                bbe = int(match['AB'].iloc[0])
                brl = float(match['Barrel%'].iloc[0])
                hh = float(match['HardHit%'].iloc[0])
                gb = float(match['GB%'].iloc[0])
                pull_air = float(match['FB%'].iloc[0])
            else:
                bbe, brl, hh, gb, pull_air = 50, 12.0, 40.0, 20.0, 20.0
            
            # THE FORMULA: Adjusted to your liking
            slam_index = min(100.0, max(5.0, (brl * 3.5) + (hh * 0.5) + (pull_air * 0.3) - (gb * 0.2)))
            
            processed_rows.append({
                "Batter Name": b['name'], "Hand": b['hand'], "BBE": bbe, 
                "💥 SLAM Index": round(slam_index, 1), "Brl %": brl, "HH %": hh, "GB %": gb
            })

        # 3. Render the final, full-lineup Table
        st.markdown(f"### ⚔️ Intent-To-Homer Lineup Analysis vs. {opposing_team}")
        df_lineup = pd.DataFrame(processed_rows).set_index("Batter Name")
        st.dataframe(df_lineup.style.apply(highlight_slam, axis=1), use_container_width=True)
        
    except Exception as e:
        st.error(f"Error processing lineup: {e}")
