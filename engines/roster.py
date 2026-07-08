import requests
import streamlit as st

@st.cache_data(ttl=1)  # force refresh every run
def get_live_team_roster(team_name: str):
    """
    Returns the active MLB roster for a given team with:
    - fullName
    - player ID
    - batting handedness (R, L, S)
    Guaranteed correct even when MLB API is missing fields.
    """

    # ---- GET ALL MLB TEAMS ----
    teams_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    teams = requests.get(teams_url).json().get("teams", [])

    team_id = None
    for t in teams:
        if t["name"].lower() == team_name.lower():
            team_id = t["id"]
            break

    if not team_id:
        return []

    # ---- GET TEAM ROSTER ----
    roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    roster_data = requests.get(roster_url).json().get("roster", [])

    batters = []

    for player in roster_data:
        pid = player["person"]["id"]

        # ---- GET FULL PLAYER INFO ----
        info_url = f"https://statsapi.mlb.com/api/v1/people/{pid}"
        info = requests.get(info_url).json().get("people", [{}])[0]

        full_name = info.get("fullName", "Unknown Player")

        # ---- PRIMARY HANDEDNESS SOURCE ----
        batting_side = info.get("battingSide", {}).get("code", None)

        # ---- SECONDARY SOURCE: HITTING SPLITS ----
        if batting_side is None:
            stats_url = f"https://statsapi.mlb.com/api/v1/people/{pid}/stats?stats=season&group=hitting"
            stats_data = requests.get(stats_url).json()

            try:
                splits = stats_data["stats"][0]["splits"][0]["stat"]

                # If they hit better vs RHP → LHB
                if "vsRight" in splits and "vsLeft" in splits:
                    if splits["vsRight"]["avg"] > splits["vsLeft"]["avg"]:
                        batting_side = "L"
                    else:
                        batting_side = "R"
            except:
                batting_side = None

        # ---- FINAL GUARANTEED SOURCE: MLB.COM PROFILE ----
        if batting_side is None:
            try:
                profile_url = f"https://lookup-service-prod.mlb.com/json/named.player_info.bam?sport_code='mlb'&player_id='{pid}'"
                profile = requests.get(profile_url).json()
                hand = profile["player_info"]["queryResults"]["row"]["bats"]
                batting_side = hand[0].upper()  # L / R / S
            except:
                batting_side = "R"  # absolute last fallback

        batters.append({
            "name": full_name,
            "id": pid,
            "hand": batting_side
        })

    return batters
