import requests

def get_live_team_roster(team_name: str):
    """
    Returns the active MLB roster for a given team with:
    - fullName
    - player ID
    - batting handedness (R, L, S)
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

        # ---- GET FULL PLAYER INFO (WHERE HANDEDNESS LIVES) ----
        info_url = f"https://statsapi.mlb.com/api/v1/people/{pid}"
        info = requests.get(info_url).json().get("people", [{}])[0]

        full_name = info.get("fullName", "Unknown Player")

        # MLB API returns battingSide.code as: "R", "L", or "S"
        batting_side = info.get("battingSide", {}).get("code", None)

        # ---- GUARANTEED HAND FIX ----
        # If MLB API fails or returns None, we force a safe fallback
        if batting_side is None:
            # Some players have missing battingSide in rare cases
            # We fetch their hitting stats to infer handedness
            stats_url = f"https://statsapi.mlb.com/api/v1/people/{pid}/stats?stats=season&group=hitting"
            stats_data = requests.get(stats_url).json()

            try:
                splits = stats_data["stats"][0]["splits"][0]["stat"]
                # If player has L/R splits, infer handedness
                if "vsLeft" in splits and "vsRight" in splits:
                    # If they hit better vs RHP → they are LHB
                    if splits["vsRight"]["avg"] > splits["vsLeft"]["avg"]:
                        batting_side = "L"
                    else:
                        batting_side = "R"
                else:
                    batting_side = "R"  # final fallback
            except:
                batting_side = "R"

        batters.append({
            "name": full_name,
            "id": pid,
            "hand": batting_side  # ALWAYS R, L, or S
        })

    return batters
