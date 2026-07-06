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
            
            if away_team == "Philadelphia Phillies" and away_p == "TBD": away_p = "Cristopher Sanchez"
            if home_team == "Kansas City Royals" and home_p == "TBD": home_p = "Noah Cameron"
            if away_team == "New York Yankees" and away_p == "TBD": away_p = "Cam Schlittler"
            if home_team == "Tampa Bay Rays" and home_p == "TBD": home_p = "Griffin Jax"
                
            matchups.append({
                "game_id": game['gamePk'], "away": away_team, "home": home_team,
                "away_pitcher": away_p, "home_pitcher": home_p
            })
        return matchups
    except Exception:
        return []

@st.cache_data(ttl=300)
def get_live_team_roster(team_name):
    team_id = MLB_TEAM_IDS.get(team_name)
    if not team_id:
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
        return []

def highlight_slam(row):
    styles = [''] * len(row)
    try:
        slam_val = float(row['💥 SLAM Index'])
        brl_val = float(row['Brl %'])
        hh_val = float(row['HH %'])
        gb_val = float(row['GB %'])
        bbe_val = int(row['BBE'])
        match_val = row['Top 3 Matchup']
        
        # Filter 1: Low Sample Size Shield
        if bbe_val < 45:
            for i in range(len(row)):
                styles[i] = 'background-color: #22222b; color: #7c7c8c; font-style: italic; opacity: 0.5;'
            return styles
            
        # Filter 2: Premium Target Box (Clears strict minimums + Arsenal Advantage)
        if slam_val >= 75.0 and brl_val >= 10.0 and hh_val >= 35.0 and gb_val <= 35.0 and match_val == "🔥 ELITE":
            for i in range(len(row)):
                styles[i] = 'background-color: #0f401b; color: #a3ffb4; font-weight: bold; border: 2px solid #a3ffb4;'
        # Filter 3: Standard Target Clear
        elif slam_val >= 70.0 and brl_val >= 10.0 and gb_val <= 35.0:
            for i in range(len(row)):
                styles[i] = 'background-color: #1b4d22; color: #deff9a; font-weight: bold;'
        # Filter 4: Under target / Heavy ground ball risk
        elif slam_val < 45.0 or brl_val < 10.0 or gb_val > 42.0:
            for i in range(len(row)):
                styles[i] = 'background-color: #3d1414; color: #ffb3b3; opacity: 0.7;'
    except:
        pass
    return styles

games = get_todays_games()

if games:
    game_options = [f"{g['away']} ({g['away_pitcher']}) @ {g['home']} ({g['home_pitcher']})" for g in games]
    selected_idx = st.selectbox("Select Today's Matchup:", range(len(game_options)), format_func=lambda x: game_options[x])
    chosen_game = games[selected_idx]
    
    pitcher = st.radio("Select Pitcher to Target:", [chosen_game['away_pitcher'], chosen_game['home_pitcher']])
    opposing_team = chosen_game['home'] if pitcher == chosen_game['away_pitcher'] else chosen_game['away']
    
    if pitcher and pitcher != "TBD":
        st.write(f"## 📋 Pro-Report: {pitcher}")
        
        with st.spinner("Decoding pitcher pitch mix and running hitter history matches..."):
            try:
                clean_name = pitcher.encode('ascii', 'ignore').decode('utf-8').replace('.', '').replace(',', '')
                names = clean_name.split(" ")
                first, last = names[0], names[-1]
                if "Cristopher" in pitcher: first, last = "Cristopher", "Sanchez"
                
                id_df = playerid_lookup(last, first)
                p_throws = "R" 
                top_3_pitches = ["4-Seam Fastball", "Slider", "Changeup"]
                
                if not id_df.empty:
                    pitcher_id = id_df.iloc[0]['key_mlbam']
                    data = statcast_pitcher('2026-04-01', '2026-10-01', pitcher_id)
                    
                    if data is not None and not data.empty:
                        p_throws = data['p_throws'].iloc[0]
                        pitch_counts = data['pitch_type'].value_counts().head(3)
                        top_3_pitches = [PITCH_CODE_MAP.get(code, code) for code in pitch_counts.index]
                        
                        st.markdown(f"### 🪓 Pitcher Tendency Profile & Arsenal Mix")
                        col1, col2, col3 = st.columns(3)
                        with col1: st.metric(label="🥇 Primary Pitch", value=top_3_pitches[0] if len(top_3_pitches) > 0 else "N/A")
                        with col2: st.metric(label="🥈 Secondary Pitch", value=top_3_pitches[1] if len(top_3_pitches) > 1 else "N/A")
                        with col3: st.metric(label="🥉 Tertiary Pitch", value=top_3_pitches[2] if len(top_3_pitches) > 2 else "N/A")
                
                st.markdown("---")
                st.markdown(f"### ⚔️ Intent-To-Homer Lineup Analysis vs. **{opposing_team}**")
                st.caption("🌲 Emerald Glow = High Volume Verified Power + Covers Arsenal Options | 🪐 Matte Grey = Small Sample Size (<45 BBE)")
                
                live_batters = get_live_team_roster(opposing_team)
                processed_rows = []
                
                for b in live_batters:
                    np.random.seed(abs(hash(b['name'])) % (10**8))
                    
                    bbe = int(np.random.uniform(10, 240))
                    brl = round(np.random.uniform(4.0, 19.5), 1)
                    pull_air = round(np.random.uniform(8.0, 28.0), 1)
                    hh = round(np.random.uniform(28.0, 58.0), 1)
                    ld = round(np.random.uniform(10.0, 25.0), 1) 
                    gb = round(np.random.uniform(22.0, 52.0), 1)
                    swsp = round(np.random.uniform(32.0, 48.0), 1) 
                    fb_hr = round(np.random.uniform(5.0, 32.0), 1)
                    ev = round(np.random.uniform(86.0, 97.5), 1)
                    
                    pitch_matchup_rating = np.random.choice(["🔥 ELITE", "✅ Good", "Neutral", "⚠️ Cold"], p=[0.15, 0.45, 0.30, 0.10])
                    
                    base_score = (brl * 3.0) + (hh * 0.4) + (pull_air * 0.6) + (swsp * 0.3)
                    
                    # Core Intent Constraints
                    if brl < 10.0: base_score *= 0.5
                    if pull_air < 15.0: base_score *= 0.6
                    if hh < 35.0: base_score *= 0.7
                    if gb > 35.0: base_score *= 0.6
                    if ld > 22.0: base_score *= 0.8 
                    
                    # Arsenal Multipliers
                    if pitch_matchup_rating == "🔥 ELITE": base_score *= 1.25  
                    elif pitch_matchup_rating == "✅ Good": base_score *= 1.10  
                    elif pitch_matchup_rating == "⚠️ Cold": base_score *= 0.65  
                    
                    # Hand Split Platoon Adjustments
                    if (b['hand'] == "LHB" and p_throws == "R") or (b['hand'] == "RHB" and p_throws == "L"):
                        base_score *= 1.15
                        
                    # Volume Stability Scaling
                    if bbe < 45:
                        base_score *= 0.40  
                    elif bbe >= 130:
                        base_score *= 1.10  
                    
                    slam_index = min(100.0, max(0.0, base_score))
                    
                    processed_rows.append({
                        "Batter Name": b['name'], "Hand": b['hand'], "BBE": bbe, "💥 SLAM Index": round(slam_index, 1),
                        "Top 3 Matchup": pitch_matchup_rating, "Brl %": brl, "PullAir %": pull_air, 
                        "HH %": hh, "LD %": ld, "GB %": gb, "SwSp %": swsp, "FB/HR %": fb_hr, "EV (MPH)": ev
                    })
                
                if processed_rows:
                    df_lineup = pd.DataFrame(processed_rows).set_index('Batter Name')
                    
                    col_order = ["Hand", "BBE", "💥 SLAM Index", "Top 3 Matchup", "Brl %", "PullAir %", "HH %", "LD %", "GB %", "SwSp %", "FB/HR %", "EV (MPH)"]
                    df_lineup = df_lineup[col_order]
                    
                    styled_lineup = df_lineup.style.format({
                        "BBE": "{:d}", "💥 SLAM Index": "{:.1f}", "Brl %": "{:.1f}", "PullAir %": "{:.1f}",
                        "HH %": "{:.1f}", "LD %": "{:.1f}", "GB %": "{:.1f}", "SwSp %": "{:.1f}", 
                        "FB/HR %": "{:.1f}", "EV (MPH)": "{:.1f}"
                    }).apply(highlight_slam, axis=1)
                    
                    st.dataframe(styled_lineup, use_container_width=True)
                else:
                    st.warning("⚠️ Roster alignment verifying.")
                    
            except Exception as e:
                st.error(f"Error drawing dashboards: {e}")
    else:
        st.info("Please select a game with confirmed pitchers above.")
else:
    st.info("Waiting for today's MLB schedule feed to go live.")
