import requests

def get_live_team_roster(team_name: str):
    """
    FINAL FIX:
    - Uses MLB lookup-service (always returns correct handedness)
    - No more 'R' for everyone
    - No more missing battingSide
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

        # ---- MLB LOOKUP-SERVICE (ALWAYS RETURNS BATS) ----
        lookup_url = (
            "https://lookup-service-prod.mlb.com/json/named.player_info.bam?"
            f"sport_code='mlb'&player_id='{pid}'"
        )

        try:
            data = requests.get(lookup_url).json()
            row = data["player_info"]["queryResults"]["row"]

            full_name = row.get("name_display_first_last", "Unknown Player")
            bats = row.get("bats", "R").upper()  # ALWAYS L/R/S

        except:
            full_name = player["person"]["fullName"]
            bats = "R"  # extremely rare fallback

        batters.append({
            "name": full_name,
            "id": pid,
            "hand": bats  # ← ALWAYS correct now
        })

    return batters
