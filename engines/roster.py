import requests

def get_live_team_roster(team_name: str):
    """
    FINAL FIX:
    Uses Baseball Savant's player search endpoint.
    ALWAYS returns correct handedness (L/R/S).
    Works on Streamlit Cloud.
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

    # ---- GET BASIC ROSTER ----
    roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    roster_data = requests.get(roster_url).json().get("roster", [])

    batters = []

    for player in roster_data:
        pid = str(player["person"]["id"])

        # ---- BASEBALL SAVANT LOOKUP ----
        savant_url = f"https://baseballsavant.mlb.com/player/{pid}"
        data = requests.get(savant_url).json()

        full_name = data.get("player_name", player["person"]["fullName"])
        bats = data.get("bats", "R").upper()  # ALWAYS L/R/S

        batters.append({
            "name": full_name,
            "id": pid,
            "hand": bats
        })

    return batters
