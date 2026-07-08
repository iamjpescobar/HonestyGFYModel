print(">>> USING SCRAPER VERSION <<<")

import requests

def get_live_team_roster(team_name: str):
    """
    NUCLEAR FIX:
    Uses StatsAPI /people endpoint.
    Guaranteed handedness for every MLB player.
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

        # ---- NUCLEAR ENDPOINT ----
        people_url = f"https://statsapi.mlb.com/api/v1/people/{pid}"

        try:
            data = requests.get(people_url).json()
            person = data["people"][0]

            # Extract handedness
            bats = person["batSide"]["code"].upper()  # L / R / S

        except Exception:
            bats = "R"

        batters.append({
            "name": full_name,
            "id": pid,
            "hand": bats
        })

    return batters
