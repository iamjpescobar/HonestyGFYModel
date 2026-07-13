"""
NPB slate fetcher — real data from npb.jp's official monthly schedule.

Parses the month's schedule/results page (verified reachable and
server-rendered from GitHub Actions) and writes data/npb/games.json
for today's slate IN JST — which, because Japan is 13 hours ahead of
US Eastern, is what a US user experiences as "tomorrow's games shown
tonight."

Every value comes straight off npb.jp: teams, stadium, start time,
status (scheduled / postponed / final with real scores). Anything the
page doesn't state (e.g. starters we can't attribute confidently) is
TBD — never guessed. NPB games can legitimately end in ties; a tied
final is reported as exactly that.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

JST = ZoneInfo("Asia/Tokyo")
EASTERN = ZoneInfo("America/New_York")

UA = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

# Japanese short names as they appear in the schedule table -> English
TEAMS = {
    "巨人": "Yomiuri Giants", "ヤクルト": "Yakult Swallows",
    "阪神": "Hanshin Tigers", "中日": "Chunichi Dragons",
    "広島": "Hiroshima Carp", "DeNA": "Yokohama DeNA BayStars",
    "日本ハム": "Nippon-Ham Fighters", "ソフトバンク": "SoftBank Hawks",
    "楽天": "Rakuten Eagles", "オリックス": "Orix Buffaloes",
    "ロッテ": "Lotte Marines", "西武": "Seibu Lions",
}

# Common stadium short names -> English (fallback: raw Japanese, still real)
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


def _en_team(jp: str) -> str:
    return TEAMS.get(jp.strip(), jp.strip())


def _en_stadium(jp: str) -> str:
    jp = jp.strip()
    return STADIUMS.get(jp, jp)


def _strip(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def fetch_month(year: int, month: int) -> str:
    url = f"https://npb.jp/games/{year}/schedule_{month:02d}_detail.html"
    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    return r.content.decode("utf-8", errors="replace")


def parse_games(html: str, year: int):
    """Yields one dict per game row in the monthly schedule table."""
    # Rows are <tr id="dateMMDD" ...> ... </tr>
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

        yield {
            "date": f"{year}-{mmdd[:2]}-{mmdd[2:]}",
            "home_jp": home_jp, "away_jp": away_jp,
            "home": _en_team(home_jp), "away": _en_team(away_jp),
            "stadium": _en_stadium(_strip(place.group(1))) if place else "TBD",
            "time_jst": time_m.group(1) if time_m else "TBD",
            "status": status,
            "home_score": home_score, "away_score": away_score,
        }


def to_et(date_str: str, time_jst: str) -> str:
    try:
        dt = datetime.strptime(f"{date_str} {time_jst}", "%Y-%m-%d %H:%M").replace(tzinfo=JST)
        return dt.astimezone(EASTERN).strftime("%-I:%M %p")
    except Exception:
        return "TBD"


def main():
    now_jst = datetime.now(JST)
    today = now_jst.strftime("%Y-%m-%d")
    html = fetch_month(now_jst.year, now_jst.month)

    all_games = list(parse_games(html, now_jst.year))
    todays = [g for g in all_games if g["date"] == today]

    games_out = []
    for g in todays:
        entry = {
            "away": g["away"], "home": g["home"],
            "stadium": g["stadium"],
            "time_jst": g["time_jst"],
            "time_et": to_et(g["date"], g["time_jst"]),
            "away_starter": "TBD", "home_starter": "TBD",
            "status": g["status"],
        }
        if g["status"] == "final":
            entry["final"] = f'{g["away"]} {g["away_score"]} - {g["home_score"]} {g["home"]}'
            if g["away_score"] == g["home_score"]:
                entry["status"] = "final (tie)"
        games_out.append(entry)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_jst": now_jst.strftime("%Y-%m-%d %H:%M"),
        "source": "npb.jp official monthly schedule",
        "slate_date_jst": today,
        "games": games_out,
    }
    (OUT / "games.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"NPB: wrote {len(games_out)} games for {today} JST "
          f"({sum(1 for g in games_out if g['status'] == 'postponed')} postponed)")
    if not games_out:
        print("NPB: empty slate — likely a league off-day. That is the honest state.")


if __name__ == "__main__":
    main()
