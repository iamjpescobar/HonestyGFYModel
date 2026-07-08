import streamlit as st
import pandas as pd
import requests
from datetime import datetime

from engines.statcast_engine import (
    get_pitcher_id,
    get_pitcher_statcast,
    build_pitch_arsenal
)

st.title("🎯 Pitcher Statcast Report")
st.markdown("---")

@st.cache_data(ttl=3600)
def get_todays_games():
    today = datetime.today().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"
    try:
        response = requests.get(url).json()
        games_list = response.get("dates", [{}])[0].get("games", [])
        matchups = []
        for g in games_list:
            matchups.append({
                "away": g["teams"]["away"]["team"]["name"],
                "home": g["teams"]["home"]["team"]["name"],
                "away_pitcher": g["teams"]["away"].get("probablePitcher", {}).get("fullName", "TBD"),
                "home_pitcher": g["teams"]["home"].get("probablePitcher", {}).get("fullName", "TBD"),
            })
        return matchups
    except:
        return []

games = get_todays_games()

if games:
    game_options = [f"{g['away']} @ {g['home']}" for g in games]
    selected_idx = st.selectbox("Select Matchup:", range(len(game_options)), format_func=lambda x: game_options[x])
    chosen = games[selected_idx]

    pitcher = st.radio("Select Pitcher:", [chosen["away_pitcher"], chosen["home_pitcher"]])

    if pitcher != "TBD":
        st.subheader(f"📋 Pitcher Report: {pitcher}")

        pitcher_id = get_pitcher_id(pitcher)
        data = get_pitcher_statcast(pitcher_id)

        st.markdown("### Pitch Arsenal")
        st.table(build_pitch_arsenal(data))
else:
    st.info("No games available.")

