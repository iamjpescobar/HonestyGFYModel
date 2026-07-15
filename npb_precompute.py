"""
NPB slate + team stats fetcher — real data from npb.jp's official
monthly schedule/results pages.

Two jobs, one verified source:
1. Today's slate IN JST (which a US user sees as tomorrow's games
   tonight), with status: scheduled / postponed / final (ties reported
   as ties).
2. Real team stats computed from every final score of the season
   (all monthly pages parsed): W-L-T record, runs scored/allowed per
   game, last-10 form, and season head-to-head for each of today's
   matchups. Every number is arithmetic on scores npb.jp printed —
   nothing modeled, nothing estimated.

Anything the source doesn't state (e.g. starters) is TBD, never guessed.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

JST = ZoneInfo("Asia/Tokyo")
EASTERN = ZoneInfo("America/New_York")
SEASON_FIRST_MONTH = 3   # NPB opens late March

UA = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

TEAMS = {
    "巨人": "Yomiuri Giants", "ヤクルト": "Yakult Swallows",
    "阪神": "Hanshin Tigers", "中日": "Chunichi Dragons",
    "広島": "Hiroshima Carp", "DeNA": "Yokohama DeNA BayStars",
    "日本ハム": "Nippon-Ham Fighters", "ソフトバンク": "SoftBank Hawks",
    "楽天": "Rakuten Eagles", "オリックス": "Orix Buffaloes",
    "ロッテ": "Lotte Marines", "西武": "Seibu Lions",
}

STADIUMS = {
    "神宮": "Jingu Stadium", "甲子園": "Koshien Stadium",
    "東京ドーム": "Tokyo Dome", "横浜": "Yokohama Stadium",
    "マツダ": "Mazda Stadium", "バンテリン": "Vantelin Dome",
    "バンテリンド": "Vantelin Dome",
    "エスコンF": "Escon Field", "PayPay": "PayPay Dome",
    "みずほPayPay": "PayPay Dome", "楽天モバイル": "Rakuten Mobile Park",
    "京セラD大阪": "Kyocera Dome Osaka", "ZOZOマリン": "Zozo Marine Stadium",
    "ベルーナD": "Belluna Dome", "ベルーナドーム": "Belluna Dome",
}

OUT = Path("build_data") / "data" / "npb"


def _avg(values):
    """Simple average that never blows up on an empty list."""
    return round(sum(values) / len(values), 2) if values else None


def _en_team(jp: str) -> str:
    return TEAMS.get(jp.strip(), jp.strip())


def _en_stadium(jp: str) -> str:
    return STADIUMS.get(jp.strip(), jp.strip())


def _strip(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def fetch_month(year: int, month: int):
    url = f"https://npb.jp/games/{year}/schedule_{month:02d}_detail.html"
    try:
        r = requests.get(url, headers=UA, timeout=25)
        if r.status_code != 200:
            return None
        return r.content.decode("utf-8", errors="replace")
    except Exception:
        return None


def parse_games(html: str, year: int):
    for m in re.finditer(r'<tr id="date(\d{4})"[^>]*>(.*?)</tr>', html, re.S):
        mmdd, row = m.group(1), m.group(2)
        team1 = re.search(r'<div class="team1">(.*?)</div>', row, re.S)
        team2 = re.search(r'<div class="team2">(.*?)</div>', row, re.S)
        if not team1 or not team2:
            continue

        home_jp, away_jp = _strip(team1.group(1)), _strip(team2.group(1))
        status, home_score, away_score = "scheduled", None, None
        if '<div class="cancel">' in row:
            status = "postponed"
        else:
            s1 = re.search(r'<div class="score1">(\d+)</div>', row)
            s2 = re.search(r'<div class="score2">(\d+)</div>', row)
            if s1 and s2:
                status = "final"
                home_score, away_score = int(s1.group(1)), int(s2.group(1))

        place = re.search(r'<div class="place">(.*?)</div>', row, re.S)
        time_m = re.search(r'<div class="time">\s*(\d{1,2}:\d{2})', row)

        # Announced starters cell — structure inside is unverified, so this
        # parses defensively: exactly two names -> home/away (home listed
        # first, matching the table's team order); anything else ships as a
        # raw "starters" string; nothing found -> TBD. The nightly log
        # prints what it saw so the assignment can be verified against
        # npb.jp by eye.
        home_sp, away_sp, sp_raw = None, None, None
        pit = re.search(r'<td[^>]*class="[^"]*pit[^"]*"[^>]*>(.*?)</td>', row, re.S)
        if pit:
            cell = re.sub(r'<br\s*/?>', '|', pit.group(1), flags=re.I)
            names = [p for p in (_strip(x) for x in cell.split('|')) if p and p != '-']
            if len(names) == 2:
                home_sp, away_sp = names[0], names[1]
            elif names:
                sp_raw = ' / '.join(names)

        yield {
            "date": f"{year}-{mmdd[:2]}-{mmdd[2:]}",
            "home": _en_team(home_jp), "away": _en_team(away_jp),
            "stadium": _en_stadium(_strip(place.group(1))) if place else "TBD",
            "time_jst": time_m.group(1) if time_m else "TBD",
            "status": status,
            "home_score": home_score, "away_score": away_score,
            "home_sp": home_sp, "away_sp": away_sp, "sp_raw": sp_raw,
        }


def to_et(date_str: str, time_jst: str) -> str:
    try:
        dt = datetime.strptime(f"{date_str} {time_jst}", "%Y-%m-%d %H:%M").replace(tzinfo=JST)
        return dt.astimezone(EASTERN).strftime("%-I:%M %p")
    except Exception:
        return "TBD"


def team_stats(finals: list) -> dict:
    """Per-team record, runs per game, last-10 — pure arithmetic on
    real final scores."""
    stats = {}
    for g in sorted(finals, key=lambda x: x["date"]):
        for side, opp_side in (("home", "away"), ("away", "home")):
            team = g[side]
            rec = stats.setdefault(team, {"w": 0, "l": 0, "t": 0,
                                          "rs": 0, "ra": 0, "g": 0,
                                          "recent": []})
            us, them = g[f"{side}_score"], g[f"{opp_side}_score"]
            rec["g"] += 1
            rec["rs"] += us
            rec["ra"] += them
            result = "T" if us == them else ("W" if us > them else "L")
            rec["w" if result == "W" else "l" if result == "L" else "t"] += 1
            rec["recent"].append(result)

    out = {}
    for team, r in stats.items():
        last10 = r["recent"][-10:]
        out[team] = {
            "record": f'{r["w"]}-{r["l"]}-{r["t"]}',
            "rs_pg": round(r["rs"] / r["g"], 2) if r["g"] else None,
            "ra_pg": round(r["ra"] / r["g"], 2) if r["g"] else None,
            "last10": f'{last10.count("W")}-{last10.count("L")}-{last10.count("T")}',
        }
    return out


def h2h(finals: list, a: str, b: str) -> dict:
    """Season head-to-head between two teams — record, every meeting's
    real scoreline, each team's average runs in those meetings, and the
    average total. All arithmetic on npb.jp's own final scores."""
    a_w = b_w = ties = 0
    a_runs, b_runs, totals, scorelines = [], [], [], []
    for g in sorted(finals, key=lambda x: x["date"]):
        pair = {g["home"], g["away"]}
        if pair != {a, b}:
            continue
        hs, as_ = g["home_score"], g["away_score"]
        a_sc = as_ if g["away"] == a else hs
        b_sc = as_ if g["away"] == b else hs
        a_runs.append(a_sc)
        b_runs.append(b_sc)
        totals.append(hs + as_)
        scorelines.append(f'{g["away"]} {g["away_score"]}-{g["home_score"]} {g["home"]} ({g["date"][5:]})')
        if hs == as_:
            ties += 1
        else:
            winner = g["home"] if hs > as_ else g["away"]
            if winner == a:
                a_w += 1
            else:
                b_w += 1
    return {"a_wins": a_w, "b_wins": b_w, "ties": ties, "games": a_w + b_w + ties,
            "a_avg_runs": _avg(a_runs), "b_avg_runs": _avg(b_runs),
            "avg_total": _avg(totals), "scorelines": scorelines}


def main():
    now_jst = datetime.now(JST)
    today = now_jst.strftime("%Y-%m-%d")

    all_games = []
    for month in range(SEASON_FIRST_MONTH, now_jst.month + 1):
        html = fetch_month(now_jst.year, month)
        if html:
            month_games = list(parse_games(html, now_jst.year))
            all_games.extend(month_games)
            print(f"  month {month:02d}: {len(month_games)} rows")

    finals = [g for g in all_games if g["status"] == "final"]
    stats = team_stats(finals)
    print(f"NPB: {len(finals)} real finals parsed across the season "
          f"({len(stats)} teams with stats)")

    todays = [g for g in all_games if g["date"] == today]
    games_out = []
    for g in todays:
        entry = {
            "away": g["away"], "home": g["home"],
            "stadium": g["stadium"],
            "time_jst": g["time_jst"],
            "time_et": to_et(g["date"], g["time_jst"]),
            "away_starter": g.get("away_sp") or "TBD",
            "home_starter": g.get("home_sp") or "TBD",
            "status": g["status"],
        }
        if g.get("sp_raw"):
            entry["starters_raw"] = g["sp_raw"]
        print(f'  [verify-starters] {g["away"]} @ {g["home"]}: '
              f'home_sp={g.get("home_sp")!r} away_sp={g.get("away_sp")!r} raw={g.get("sp_raw")!r}')
        if g["status"] == "final":
            entry["final"] = f'{g["away"]} {g["away_score"]} - {g["home_score"]} {g["home"]}'
            if g["away_score"] == g["home_score"]:
                entry["status"] = "final (tie)"

        for side in ("away", "home"):
            s = stats.get(g[side])
            if s:
                entry[f"{side}_record"] = s["record"]
                entry[f"{side}_rs_pg"] = s["rs_pg"]
                entry[f"{side}_ra_pg"] = s["ra_pg"]
                entry[f"{side}_last10"] = s["last10"]

        hh = h2h(finals, g["away"], g["home"])
        if hh["games"] > 0:
            ties_bit = f'-{hh["ties"]}' if hh["ties"] else ""
            entry["h2h"] = (f'{g["away"]} {hh["a_wins"]}-{hh["b_wins"]}{ties_bit} '
                            f'{g["home"]} (2026, {hh["games"]} games)')
            entry["h2h_detail"] = {
                "avg_total": hh["avg_total"],
                "away_avg_runs": hh["a_avg_runs"],
                "home_avg_runs": hh["b_avg_runs"],
                "scorelines": hh["scorelines"],
            }
        games_out.append(entry)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_jst": now_jst.strftime("%Y-%m-%d %H:%M"),
        "source": "npb.jp official monthly schedule/results",
        "slate_date_jst": today,
        "games": games_out,
    }
    (OUT / "games.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"NPB: wrote {len(games_out)} games for {today} JST")
    if not games_out:
        print("NPB: empty slate — likely a league off-day. That is the honest state.")


if __name__ == "__main__":
    main()