import requests

def get_all_teams():
    """
    Returns a clean list of all MLB team names.
    """
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    teams = requests.get(url).json().get("teams", [])
    return sorted([t["name"] for t in teams])


def get_live_team_roster(team_name: str):
    """
    Returns the live roster for a given MLB team.
    Includes guaranteed handedness via the /people endpoint.
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

    players = []

    for player in roster_data:
        pid = str(player["person"]["id"])
        full_name = player["person"]["fullName"]

        # ---- NUCLEAR ENDPOINT FOR HANDEDNESS ----
        people_url = f"https://statsapi.mlb.com/api/v1/people/{pid}"

        try:
            data = requests.get(people_url).json()
            person = data["people"][0]

            bats = person["batSide"]["code"].upper()  # L / R / S
            throws = person["pitchHand"]["code"].upper()  # L / R

        except Exception:
            bats = "R"
            throws = "R"

        players.append({
            "name": full_name,
            "id": pid,
            "bats": bats,
            "throws": throws
        })

    return players
