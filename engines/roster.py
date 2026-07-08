print(">>> USING SCRAPER VERSION <<<")

import requests
from bs4 import BeautifulSoup

def get_live_team_roster(team_name: str):
    """
    Updated MLB.com scraper — works with the new 2026 layout.
    Extracts handedness from the JSON-LD block instead of page text.
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

        # ---- SCRAPE MLB.COM PLAYER PAGE ----
        mlb_url = f"https://www.mlb.com/player/{full_name.replace(' ', '-').lower()}-{pid}"

        try:
            html = requests.get(mlb_url).text
            soup = BeautifulSoup(html, "html.parser")

            # MLB now stores handedness inside a JSON-LD script block
            json_ld = soup.find("script", type="application/ld+json")

            bats = "R"  # default fallback

            if json_ld:
                import json
                data = json.loads(json_ld.text)

                # Look for "batSide" field
                if "batSide" in data and "code" in data["batSide"]:
                    code = data["batSide"]["code"].upper()
                    if code in ["L", "R", "S"]:
                        bats = code

        except Exception:
            bats = "R"

        batters.append({
            "name": full_name,
            "id": pid,
            "hand": bats
        })

    return batters
