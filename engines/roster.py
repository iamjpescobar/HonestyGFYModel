import requests

def get_live_team_roster(team_name: str):
    """
    Fast + reliable roster fetch:
    - correct handedness (R/L/S)
    - only ONE API call
    - no freezing on Streamlit Cloud
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

    # ---- EXPANDED ROSTER (includes handedness!) ----
    roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?hydrate=person"
    roster_data = requests.get(roster_url).json().get("roster", [])

    batters = []

    for player in roster_data:
        person = player.get("person", {})

        full_name = person.get("fullName", "Unknown Player")
        pid = person.get("id", None)

        # MLB API returns battingSide.code as: "R", "L", "S"
        batting_side = person.get("battingSide", {}).get("code", "R")

        batters.append({
            "name": full_name,
            "id": pid,
            "hand": batting_side
        })

    return batters
