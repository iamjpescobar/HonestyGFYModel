import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# KC THEME
# ---------------------------------------------------------
from app.styles.kc_theme import inject_kc_theme

# ---------------------------------------------------------
# ENGINES
# ---------------------------------------------------------
from app.engines.roster import get_all_teams, get_live_team_roster
from app.engines.batter_stats import load_batting_stats, get_batter_profile
from app.engines.statcast_engine import (
    get_pitcher_id,
    get_pitcher_statcast,
    build_pitch_arsenal
)
from app.engines.danger_zone import build_danger_zone
from app.engines.pitcher_danger_zone import build_pitcher_danger_zone
from app.engines.matchup_engine import compute_matchup_multiplier
from app.engines.slam_engine import compute_slam_index
from app.engines.pitch_affinity_engine import compute_pitch_affinity_multiplier
from app.engines.bvp_engine import get_bvp_history

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="KC Lineup Engine",
    page_icon="🟦",
    layout="wide"
)

inject_kc_theme()

# ---------------------------------------------------------
# SIDEBAR — TEAM + PLAYER SELECTOR
# ---------------------------------------------------------
st.sidebar.header("KC Lineup Engine")

teams = get_all_teams()
selected_team = st.sidebar.selectbox("Choose a Team", teams)

team_roster = get_live_team_roster(selected_team)
player_list = [p["name"] for p in team_roster]

selected_player = st.sidebar.selectbox("Choose a Player", player_list)

# ---------------------------------------------------------
# BUILD BATTER PROFILE
# ---------------------------------------------------------
stats_df = load_batting_stats()
batter_profile = get_batter_profile(selected_player, stats_df)

# ---------------------------------------------------------
# BUILD PITCHER PROFILE (STATCAST + ARSENAL)
# ---------------------------------------------------------
pitcher_id = get_pitcher_id(selected_player)
pitcher_data = get_pitcher_statcast(pitcher_id)
pitcher_arsenal = build_pitch_arsenal(pitcher_data)

pitcher_profile = {
    "Pitcher ID": pitcher_id,
    "Arsenal": pitcher_arsenal
}

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown(
    """
    <h1 class="main-header">KC Lineup Engine</h1>
    <h3 class="sub-header">Los Cappers Sabermetric Model</h3>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# BATTER DANGER ZONE
# ---------------------------------------------------------
st.subheader("Batter Danger Zone")
danger_grid = build_danger_zone(batter_profile)
st.dataframe(danger_grid, use_container_width=True)

# ---------------------------------------------------------
# PITCHER DANGER ZONE
# ---------------------------------------------------------
st.subheader("Pitcher Danger Zone")
pitcher_grid = build_pitcher_danger_zone(pitcher_profile)
st.dataframe(pitcher_grid, use_container_width=True)

# ---------------------------------------------------------
# MATCHUP ENGINE
# ---------------------------------------------------------
st.subheader("Matchup Engine")
matchup_mult, matchup_tag = compute_matchup_multiplier(
    batter_profile,
    pitcher_profile
)
st.write(f"Matchup Multiplier: {matchup_mult:.2f} — {matchup_tag}")

# ---------------------------------------------------------
# SLAM ENGINE
# ---------------------------------------------------------
st.subheader("SLAM Score")
slam_score = compute_slam_index(batter_profile, pitcher_profile)
st.write(f"SLAM Score: {slam_score:.2f}")

# ---------------------------------------------------------
# PITCH AFFINITY ENGINE
# ---------------------------------------------------------
st.subheader("Pitch Affinity")
affinity_mult = compute_pitch_affinity_multiplier(
    batter_profile,
    pitcher_arsenal
)
st.write(f"Pitch Affinity Multiplier: {affinity_mult:.2f}")

# ---------------------------------------------------------
# BVP ENGINE
# ---------------------------------------------------------
st.subheader("BVP History")
bvp_history = get_bvp_history(selected_player, selected_player)
st.dataframe(bvp_history, use_container_width=True)

# ---------------------------------------------------------
# PITCHER ARSENAL (KC CARD STYLE)
# ---------------------------------------------------------
st.subheader("Pitcher Arsenal (KC Style)")
st.dataframe(pitcher_arsenal, use_container_width=True)
