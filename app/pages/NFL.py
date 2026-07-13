import streamlit as st

from styles.kc_theme import inject_kc_theme
from auth import require_login

# Page meta
st.set_page_config(page_title="NFL Analytics", page_icon="🏈", layout="wide")

# Theme + auth
inject_kc_theme()
require_login()

# Page header
st.title("NFL Analytics")
st.markdown("Comprehensive NFL matchup, player, and betting insights — NFL engine coming soon.")

# Layout: left selectors, main content, right insights
left_col, main_col, right_col = st.columns([1, 3, 1])

with left_col:
    st.subheader("Select Game")
    # TODO: Replace with your real game picker widget / data source
    game_date = st.date_input("Game date")
    home_team = st.selectbox("Home team", ["PIT", "GB", "NE", "DAL"], index=0)
    away_team = st.selectbox("Away team", ["NYG", "CHI", "MIA", "KC"], index=1)

    st.markdown("---")
    st.subheader("Select Player")
    # TODO: Replace with dynamic roster loader
    team_side = st.radio("Side", ["Home", "Away"])
    player = st.selectbox("Player", ["Player A", "Player B", "Player C"])

    st.markdown("---")
    st.subheader("Filters")
    st.checkbox("Show advanced metrics", value=True)
    st.checkbox("Include weather adjustments", value=False)

with main_col:
    st.header("Matchup Card")
    st.info("This area mirrors the MLB Game Card layout. Replace placeholders with NFL engine outputs.")
    # Top summary
    st.markdown("**Game:** {} @ {} — {}".format(away_team, home_team, game_date))
    st.markdown("**Selected player:** {} ({})".format(player, team_side))

    # Two-column matchup details
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Team Overview")
        st.write("Offense/Defense ratings, pace, situational splits.")
        st.table({"Metric": ["Off Rating", "Def Rating"], "Value": [None, None]})
    with col_b:
        st.subheader("Player Overview")
        st.write("QB/RB/WR advanced metrics, snap share, target share.")
        st.table({"Metric": ["EPA/play", "Success Rate"], "Value": [None, None]})

    st.markdown("---")
    st.subheader("Matchup Visuals")
    st.write("Placeholder for matchup charts (routes vs coverage, pass rush vs OL).")
    # TODO: Insert charts and visual components used by MLB GameCard

with right_col:
    st.subheader("Betting Insights")
    st.metric("Implied Win %", "—")
    st.metric("Edge (EV)", "—")
    st.markdown("**Lines**")
    st.write("Open: —  |  Close: —")
    st.markdown("---")
    st.subheader("Quick Notes")
    st.write("- Weather: TBD\n- Injuries: TBD\n- Line movement: TBD")

# Footer / debug
st.markdown("---")
st.caption("NFL page scaffolded to match MLB Game Card structure. TODO: hook NFL data engines.")
