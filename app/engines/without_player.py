"""
Without-player splits — how a team performs when someone is out.

The question this answers: "X is sitting tonight; who eats those
minutes and shots, and does the team score more or less?" It's one of
the sharpest edges in basketball props, and it's computable from data
already collected — no new fetching.

HOW IT WORKS
Every per-game log line in the WNBA pipeline exists only when a player
actually played (lines with zero minutes are dropped upstream). So for
any team, the set of dates its players appear on IS the team's game
list, and the dates a specific player is missing from are the games he
sat. Comparing a teammate's production across those two date sets is
pure arithmetic on real box scores.

WHAT IT REPORTS
For the selected absent player, per remaining teammate:
  - per-game production WITH him (points / rebounds / assists / PRA)
  - per-game production WITHOUT him
  - the delta, and the games behind each side
Plus a team-level line: points scored per game with and without.

SAMPLE FLOORS
A "without" split off two games is an anecdote, not a signal. Nothing
is reported below MIN_WITHOUT games, and every row shows both sample
sizes so a 4-game split is never mistaken for a 20-game one. Teammates
who themselves played too few games either way are excluded.

This is descriptive, not predictive: it says what happened when he sat,
which is usually driven by role changes that persist — but it can also
reflect who the opponents happened to be. The page says so.
"""

MIN_WITHOUT = 3      # games the player missed before a split is shown
MIN_TEAMMATE_GP = 8  # a teammate's own total games before he's listed

_STATS = ("pts", "reb", "ast", "pra")


def _avg(vals):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), 1) if vals else None


def team_players(logs, team):
    """[(pid, name, games_played)] for one team, most-played first."""
    out = []
    for pid, rec in (logs or {}).items():
        if rec.get("team") != team:
            continue
        n = len(rec.get("games") or [])
        if n:
            out.append((pid, rec.get("name") or rec.get("full_name") or "?", n))
    out.sort(key=lambda x: -x[2])
    return out


def team_game_dates(logs, team):
    """Every date this team played, from its players' logs."""
    dates = set()
    for _pid, rec in (logs or {}).items():
        if rec.get("team") != team:
            continue
        for gl in rec.get("games") or []:
            d = gl.get("date")
            if d:
                dates.add(d)
    return dates


def without_player(logs, team, out_pid):
    """(rows, meta) — teammate production with vs without out_pid."""
    all_dates = team_game_dates(logs, team)
    played = {gl.get("date") for gl in (logs.get(out_pid, {}).get("games") or [])
              if gl.get("date")}
    missed = all_dates - played

    meta = {
        "team": team,
        "player": (logs.get(out_pid) or {}).get("name", "?"),
        "team_games": len(all_dates),
        "games_with": len(played),
        "games_without": len(missed),
        "enough": len(missed) >= MIN_WITHOUT,
        "min_without": MIN_WITHOUT,
    }
    if not meta["enough"]:
        return [], meta

    rows = []
    for pid, rec in (logs or {}).items():
        if rec.get("team") != team or pid == out_pid:
            continue
        games = rec.get("games") or []
        if len(games) < MIN_TEAMMATE_GP:
            continue
        with_games = [g for g in games if g.get("date") in played]
        without_games = [g for g in games if g.get("date") in missed]
        if not without_games:
            continue

        row = {"name": rec.get("name") or "?",
               "pos": rec.get("pos") or "?",
               "n_with": len(with_games),
               "n_without": len(without_games)}
        for stat in _STATS:
            w = _avg([g.get(stat) for g in with_games])
            wo = _avg([g.get(stat) for g in without_games])
            row[f"with_{stat}"] = w
            row[f"without_{stat}"] = wo
            row[f"delta_{stat}"] = (round(wo - w, 1)
                                    if w is not None and wo is not None else None)
        # minutes tell the role story behind the production change
        row["with_min"] = _avg([g.get("min") for g in with_games])
        row["without_min"] = _avg([g.get("min") for g in without_games])
        row["delta_min"] = (round(row["without_min"] - row["with_min"], 1)
                            if row["with_min"] is not None
                            and row["without_min"] is not None else None)
        rows.append(row)

    # team scoring per game, both ways
    def _team_pts(dates):
        by_date = {}
        for _pid, rec in (logs or {}).items():
            if rec.get("team") != team:
                continue
            for gl in rec.get("games") or []:
                d = gl.get("date")
                if d in dates:
                    by_date[d] = by_date.get(d, 0) + (gl.get("pts") or 0)
        return _avg(list(by_date.values()))

    meta["team_pts_with"] = _team_pts(played)
    meta["team_pts_without"] = _team_pts(missed)
    if meta["team_pts_with"] is not None and meta["team_pts_without"] is not None:
        meta["team_pts_delta"] = round(meta["team_pts_without"] - meta["team_pts_with"], 1)
    else:
        meta["team_pts_delta"] = None

    rows.sort(key=lambda r: -(r.get("delta_pra") if r.get("delta_pra") is not None else -99))
    return rows, meta
