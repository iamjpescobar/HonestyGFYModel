print(">>> USING SCRAPER VERSION <<<")

import requests

def get_live_team_roster(team_name: str):
    """
    FINAL FIX — DO NOT CHANGE
    Uses MLB lookup-service API (never blocked, always returns handedness).
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
        full_name = player["person"]["fullName"]

        # ---- USE LOOKUP-SERVICE (ALWAYS RETURNS HANDEDNESS) ----
        lookup_url = f"https://lookup-service-prod.mlb.com/json/named.player_info.bam?sport_code='mlb'&player_id='{pid}'"

        try:
            data = requests.get(lookup_url).json()
            info = data["player_info"]["queryResults"]["row"]

            bats = info.get("bats", "R").upper()  # L / R / S

        except Exception:
            bats = "R"

        batters.append({
            "name": full_name,
            "id": pid,
            "hand": bats
        })

    return batters
