import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pybaseball import statcast_pitcher, playerid_lookup

st.set_page_config(layout="wide")

st.title("⚾ Daily Matchup Analyst")
st.markdown("---")

# 1. FETCH TODAY'S MATCHUPS (FREE MLB API)
@st.cache_data(ttl=3600)  # Refreshes every hour automatically
def get_todays_games():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date={today}"
    try:
        response = requests.get(url).json()
        games = response.get('dates', [{}])[0].get('games', [])
        
        matchups = []
        for game in games:
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            
            away_pitcher = game['teams']['away'].get('probablePitcher', {}).get('name', 'TBD')
            home_pitcher = game['teams']['home'].get('probablePitcher', {}).get('name', 'TBD')
            
            # ─── FULL DAILY SCHEDULE OVERRIDES FOR JULY 6, 2026 ───
            if away_team == "Philadelphia Phillies" and away_pitcher == "TBD": away_pitcher = "Cristopher Sanchez"
            if home_team == "Kansas City Royals" and home_pitcher == "TBD": home_pitcher = "Noah Cameron"
            
            if away_team == "New York Yankees" and away_pitcher == "TBD": away_pitcher = "Cam Schlittler"
            if home_team == "Tampa Bay Rays" and home_pitcher == "TBD": home_pitcher = "Griffin Jax"
            
            if away_team == "Houston Astros" and away_pitcher == "TBD": away_pitcher = "Mike Burrows"
            if home_team == "Washington Nationals" and home_pitcher == "TBD": home_pitcher = "Miles Mikolas"
            
            if away_team == "New York Mets" and away_pitcher == "TBD": away_pitcher = "Freddy Peralta"
            if home_team == "Atlanta Braves" and home_pitcher == "TBD": home_pitcher = "Reynaldo Lopez"
            
            if away_team == "Milwaukee Brewers" and away_pitcher == "TBD": away_pitcher = "Shane Drohan"
            if home_team == "St. Louis Cardinals" and home_pitcher == "TBD": home_pitcher = "Dustin May"
            
            if away_team == "Arizona Diamondbacks" and away_pitcher == "TBD": away_pitcher = "Brandon Pfaadt"
            if home_team == "San Diego Padres" and home_pitcher == "TBD": home_pitcher = "Walker Buehler"
            
            if away_team == "Toronto Blue Jays" and away_pitcher == "TBD": away_pitcher = "Kevin Gausman"
            if home_team == "San Francisco Giants" and home_pitcher == "TBD": home_pitcher = "Landen Roupp"
            
            if away_team == "Colorado Rockies" and away_pitcher == "TBD": away_pitcher = "Kyle Freeland"
            if home_team == "Los Angeles Dodgers" and home_pitcher == "TBD": home_pitcher = "Eric Lauer"
                
            matchups.append({
                "game_id": game['gamePk'],
                "away": away_team,
                "home": home_team,
                "away_pitcher": away_pitcher,
                "home_pitcher": home_pitcher
            })
        return matchups
    except:
        return []

games = get_todays_games()

if not games:
    st.warning("No games found for today or MLB API is down.")
else:
    game_options = [f"{g['away']} @ {g['home']} | Pitchers: {g['away_pitcher']} vs {g['home_pitcher']}" for g in games]
    selected_game_idx = st.selectbox("Select Today's Matchup:", range(len(game_options)), format_func=lambda x: game_options[x])
    
    chosen_game = games[selected_game_idx]
    
    pitcher_to_analyze = st.radio("Select Pitcher to Target:", [chosen_game['away_pitcher'], chosen_game['home_pitcher']])
    with st.spinner("Crunching Statcast data for free..."):
            try:
                # Clean up accents automatically so the database can read it cleanly
                # (e.g., converts 'Sánchez' to 'Sanchez')
                clean_name = pitcher_to_analyze.encode('ascii', 'ignore').decode('utf-8')
                names = clean_name.split(" ")
                first, last = names[0], names[-1]
                
                # Special manual safety check for Cristopher
                if "Cristopher" in pitcher_to_analyze:
                    first, last = "Cristopher", "Sanchez"
                
                id_df = playerid_lookup(last, first)
                if not id_df.empty:
                    pitcher_id = id_df.iloc[0]['key_mlbam']
                    
                    data = statcast_pitcher('2026-04-01', '2026-10-01', pitcher_id)
                    
                    if not data.empty:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📊 Current Pitch Mix %")
                            pitch_counts = data['pitch_type'].value_counts(normalize=True) * 100
                            st.dataframe(pitch_counts.rename("Mix %"))
                        
                        with col2:
                            st.markdown("#### 🎯 Pitcher Weak Spots (Hard Hit Pitches)")
                            hard_hits = data[data['launch_speed'] > 95]
                            weak_pitches = hard_hits['pitch_type'].value_counts(normalize=True) * 100
                            st.write("Pitches giving up the most hard-hit contact (>95 MPH):")
                            st.dataframe(weak_pitches.rename("Hard Hit Share %"))
                    else:
                        st.error("No recent Statcast data found for this player yet.")
                else:
                    st.error("Could not locate Player ID.")
            except Exception as e:
                st.error(f"Error compiling data: {e}")
    
