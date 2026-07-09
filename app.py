import streamlit as st
import pandas as pd

# --- KC THEME ---
from styles.kc_theme import inject_kc_theme
inject_kc_theme()

# --- ENGINES ---
from engines.statcast_engine import (
    get_pitcher_id,
    get_pitcher_statcast,
    build_pitch_arsenal
)

from engines.batter_stats import (
    load_batting_stats,
    get_batter_profile
)

from engines.matchup_engine import compute_matchup_multiplier
from engines.pitch_affinity_engine import compute_pitch_affinity_multiplier
from engines.slam_engine import compute_slam_index

from engines.danger_zone import build_danger_zone
from engines.pitcher_danger_zone import build_pitcher_danger_zone

from engines.roster import get_live_team_roster


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Los Cappers Lab — KC Home Hub",
    page_icon="🧪"
)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown('<div class="main-header">LOS CAPPERS LAB</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">The Advanced S.L.A.M. Index Analytics Hub</div>', unsafe_allow_html=True)
st.markdown("---")


# ---------------------------------------------------------
# INPUTS — PITCHER + TEAM
# ---------------------------------------------------------
colA, colB = st.columns(2)

with colA:
    pitcher_name = st.text_input("🎯 Enter Pitcher Name:", "")

with colB:
    team_name = st.text_input("⚔️ Enter Opposing Team:", "")


if pitcher_name and team_name:

    # ---------------------------------------------------------
    # PITCHER PROFILE + ARSENAL
    # ---------------------------------------------------------
    st.markdown("## 📋 Pitcher Pro-Report")

    pitcher_id = get_pitcher_id(pitcher_name)
    pitcher_data = get_pitcher_statcast(pitcher_id)

    arsenal_df = build_pitch_arsenal(pitcher_data)
    st.markdown("### 🎯 Verified Pitch Arsenal Distribution")
    st.dataframe(arsenal_df, use_container_width=True)

    # Pitcher danger zone
    pitcher_profile = {
        "HR/BBE": pitcher_data.get("hr_rate", 0),
        "HH %": pitcher_data.get("hard_hit_rate", 0),
        "LD %": pitcher_data.get("line_drive_rate", 0),
        "Brl %": pitcher_data.get("barrel_rate", 0),
        "ZoneContact %": pitcher_data.get("zone_contact", 0)
    }

    pdz = build_pitcher_danger_zone(pitcher_profile)
    pdz_reset = pdz.reset_index().melt(id_vars="index")
    pdz_reset.columns = ["Vertical", "Horizontal", "Danger"]

    st.markdown("### 🔥 Pitcher Danger Zone Heatmap")
    st.altair_chart(
        alt.Chart(pdz_reset)
        .mark_rect()
        .encode(
            x="Horizontal:N",
            y="Vertical:N",
            color=alt.Color("Danger:Q", scale=alt.Scale(scheme="reds")),
            tooltip=["Vertical", "Horizontal", "Danger"]
        )
        .properties(width=300, height=300),
        use_container_width=False
    )

    # ---------------------------------------------------------
    # LINEUP ANALYSIS
    # ---------------------------------------------------------
    st.markdown(f"## ⚔️ Intent-To-Homer Lineup Analysis vs. {team_name}")

    live_batters = get_live_team_roster(team_name)
    stats_df = load_batting_stats()

    processed_rows = []

    for b in live_batters:
        prof = get_batter_profile(b["name"], stats_df)

        # matchup engine
        matchup_mult, matchup_tag = compute_matchup_multiplier(prof, pitcher_profile)

        # pitch affinity engine
        pitch_affinity_mult = compute_pitch_affinity_multiplier(prof, arsenal_df)

        # SLAM
        slam = compute_slam_index(
            brl=prof["Brl %"],
            hh=prof["HH %"],
            pull_air=prof["PullAir %"],
            ld=prof["LD %"],
            gb=prof["GB %"],
            bbe=prof["BBE"],
            matchup_mult=matchup_mult,
            pitch_affinity_mult=pitch_affinity_mult
        )

        processed_rows.append({
            "Batter": b["name"],
            "Hand": b["hand"],
            "BBE": prof["BBE"],
            "SLAM": round(slam, 1),
            "Matchup": matchup_tag,
            "Brl %": prof["Brl %"],
            "HH %": prof["HH %"],
            "PullAir %": prof["PullAir %"],
            "LD %": prof["LD %"],
            "GB %": prof["GB %"],
        })

    df = pd.DataFrame(processed_rows).set_index("Batter")

    st.dataframe(df, use_container_width=True)

    # ---------------------------------------------------------
    # SCOUT CARD
    # ---------------------------------------------------------
    st.markdown("### 🔍 KC Scout Card")

    selected = st.selectbox("Select Batter:", ["--"] + list(df.index))

    if selected != "--":
        sb = df.loc[selected]

        st.markdown(f"## 📊 {selected} — Full KC Breakdown")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SLAM Index", sb["SLAM"])
        c2.metric("Barrel %", f"{sb['Brl %']}%")
        c3.metric("Hard Hit %", f"{sb['HH %']}%")
        c4.metric("BBE Sample", sb["BBE"])

        st.markdown("### 🔋 Power Profile")
        st.write(f"- PullAir %: {sb['PullAir %']}%")
        st.write(f"- Line Drive %: {sb['LD %']}%")
        st.write(f"- Groundball %: {sb['GB %']}%")

        st.markdown("### ⚔️ Matchup Tag")
        st.write(f"**{sb['Matchup']}**")

        # Batter danger zone
        dz = build_danger_zone(sb)
        dz_reset = dz.reset_index().melt(id_vars="index")
        dz_reset.columns = ["Vertical", "Horizontal", "Danger"]

        st.markdown("### 🔥 Batter Danger Zone Heatmap")
        st.altair_chart(
            alt.Chart(dz_reset)
            .mark_rect()
            .encode(
                x="Horizontal:N",
                y="Vertical:N",
                color=alt.Color("Danger:Q", scale=alt.Scale(scheme="purples")),
                tooltip=["Vertical", "Horizontal", "Danger"]
            )
            .properties(width=300, height=300),
            use_container_width=False
        )

else:
    st.info("Enter a pitcher and team to begin KC analysis.")
