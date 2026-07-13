import streamlit as st

from styles.kc_theme import inject_kc_theme
from auth import require_login

# Page meta
st.set_page_config(page_title="NBA Analytics", page_icon="🏀", layout="wide")

# Theme + auth
inject_kc_theme()
require_login()

# Page header
st.title("NBA Analytics")
st.markdown("NBA matchup and player analytics — engine to be connected.")

# Layout: left selectors, main content, right insights
left_col, main_col, right_col = st.columns([1, 3, 1])

with left_col:
    st.subheader("Select Game")
    game_date = st.date_input("Game date")
    home_team = st.selectbox("Home team", ["LAL", "BOS", "GSW", "MIA"], index=0)
    away_team = st.selectbox("Away team", ["NYK", "CHI", "PHI", "DAL"], index=1)

    st.markdown("---")
    st.subheader("Select Player")
    team_side = st.radio("Side", ["Home", "Away"])
    player = st.selectbox("Player", ["Player X", "Player Y", "Player Z"])

    st.markdown("---")
    st.subheader("Filters")
    st.checkbox("Show advanced metrics", value=True)
    st.checkbox("Include lineup rotations", value=True)

with main_col:
    st.header("Matchup Card")
    st.info("Mirrors MLB Game Card layout; replace placeholders with NBA engine outputs.")
    st.markdown("**Game:** {} @ {} — {}".format(away_team, home_team, game_date))
    st.markdown("**Selected player:** {} ({})".format(player, team_side))

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Team Overview")
        st.write("Offensive/Defensive ratings, pace, shot profile.")
        st.table({"Metric": ["Off Rating", "Def Rating"], "Value": [None, None]})
    with col_b:
        st.subheader("Player Overview")
        st.write("Usage, TS%, PER, defensive impact.")
        st.table({"Metric": ["Usage", "TS%"], "Value": [None, None]})

    st.markdown("---")
    st.subheader("Matchup Visuals")
    st.write("Placeholder for shot charts, matchup on/off splits.")
    # TODO: Insert charts and visual components used by MLB GameCard

with right_col:
    st.subheader("Betting Insights")
    st.metric("Implied Win %", "—")
    st.metric("Edge (EV)", "—")
    st.markdown("**Lines**")
    st.write("Spread: —  |  Total: —")
    st.markdown("---")
    st.subheader("Quick Notes")
    st.write("- Rest days: TBD\n- Injuries: TBD\n- Rotation changes: TBD")

st.markdown("---")
st.caption("NBA page scaffolded to match MLB Game Card structure. TODO: hook NBA data engines.")
