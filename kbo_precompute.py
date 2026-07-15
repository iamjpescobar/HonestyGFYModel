"""
KBO slate + season data fetcher — real data from MyKBOStats.

v2 adds the season layer: crawls every week's schedule page since
opening day, parses finals DEFENSIVELY (the score markup inside past
game-lines was never captured in recon, so this attempts a conservative
pattern, prints a sample of what it saw to the Actions log for
verification, and — if nothing parses — simply omits team stats and
H2H rather than shipping anything invented).

When finals DO parse, each of today's games carries: both teams' real
record, runs scored/allowed per game, last-10 form, and the season
head-to-head — record, every meeting's scoreline, each team's average
runs in those meetings, and the average total.
"""

import json
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

KST = ZoneInfo("Asia/Seoul")
EASTERN = ZoneInfo("America/New_York")
SEASON_START = date(2026, 3, 17)   # first crawl week; pre-season weeks just parse empty

UA = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}

TEAMS = {
    "Kia": "Kia Tigers", "KT": "KT Wiz", "LG": "LG Twins",
    "Lotte": "Lotte Giants", "Doosan": "Doosan Bears", "NC": "NC Dinos",
    "Kiwoom": "Kiwoom Heroes", "Hanwha": "Hanwha Eagles",
    "Samsung": "Samsung Lions", "SSG": "SSG Landers",
}

OUT = Path("build_data") / "data" / "kbo"

GAME_LINE = re.compile(
    r'<a id="game-line-\d+" class="game-line" '
    r'href="/games/\d+-([A-Za-z]+)-vs-([A-Za-z]+)-(\d{8})">(.*?)</a>',
    re.S,
)
# Conservative score pattern: two 1-2 digit numbers joined by a dash,
# NOT part of a time (times use ":") and not digit-adjacent.
SCORE_PAT = re.compile(r'(?<![\d:])(\d{1,2})\s*-\s*(\d{1,2})(?![\d:])')


def _team(short):
    return TEAMS.get(short, short)


def _strip(html):
    return re.sub(r"<[^>]+>", " ", html)


def fetch(url):
    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    return r.content.decode("utf-8", errors="replace")


def parse_week(html, today_str, sample_holder):
    """Yields game dicts from one week page. Scores parsed defensively."""
    for m in GAME_LINE.finditer(html):
        away_short, home_short, yyyymmdd, inner = m.groups()
        gdate = f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"

        dt_utc = None
        t = re.search(r'datetime="([0-9T:+.Z-]+)"', inner)
        if t:
            try:
                dt_utc = datetime.fromisoformat(t.group(1).replace("Z", "+00:00"))
            except ValueError:
                pass

        venue = re.search(r'<div class="venue">\s*(.*?)\s*</div>', inner, re.S)

        g = {
            "date": gdate,
            "away": _team(away_short), "home": _team(home_short),
            "stadium": re.sub(r"\s+", " ", _strip(venue.group(1))).strip() if venue else "TBD",
            "time_kst": dt_utc.astimezone(KST).strftime("%H:%M") if dt_utc else "TBD",
            "time_et": dt_utc.astimezone(EASTERN).strftime("%-I:%M %p") if dt_utc else "TBD",
            "status": "scheduled",
        }

        if gdate < today_str:
            text = re.sub(r"\s+", " ", _strip(inner))
            if sample_holder and sample_holder.get("sample") is None:
                sample_holder["sample"] = text[:400]
            sm = SCORE_PAT.search(text)
            if sm:
                # Away is listed first on the page, so away-home order.
                g["away_score"], g["home_score"] = int(sm.group(1)), int(sm.group(2))
                g["status"] = "final"
        yield g


def _avg(vals):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else None


def team_form(finals):
    per = {}
    for g in sorted(finals, key=lambda x: x["date"]):
        for side, opp in (("home", "away"), ("away", "home")):
            t = per.setdefault(g[side], {"w": 0, "l": 0, "t": 0, "rs": [], "ra": [], "res": []})
            us, them = g[f"{side}_score"], g[f"{opp}_score"]
            t["rs"].append(us)
            t["ra"].append(them)
            r = "T" if us == them else ("W" if us > them else "L")
            t["w" if r == "W" else "l" if r == "L" else "t"] += 1
            t["res"].append(r)
    out = {}
    for team, t in per.items():
        l10 = t["res"][-10:]
        ties = f'-{t["t"]}' if t["t"] else ""
        out[team] = {
            "record": f'{t["w"]}-{t["l"]}{ties}',
            "rs_pg": _avg(t["rs"]), "ra_pg": _avg(t["ra"]),
            "last10": f'{l10.count("W")}-{l10.count("L")}'
                      + (f'-{l10.count("T")}' if l10.count("T") else ""),
        }
    return out


def h2h(finals, a, b):
    a_w = b_w = ties = 0
    a_runs, b_runs, totals, scorelines = [], [], [], []
    for g in sorted(finals, key=lambda x: x["date"]):
        if {g["home"], g["away"]} != {a, b}:
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
        elif (g["home"] if hs > as_ else g["away"]) == a:
            a_w += 1
        else:
            b_w += 1
    games = a_w + b_w + ties
    if not games:
        return None
    return {"a_wins": a_w, "b_wins": b_w, "ties": ties, "games": games,
            "a_avg_runs": _avg(a_runs), "b_avg_runs": _avg(b_runs),
            "avg_total": _avg(totals), "scorelines": scorelines}


def main():
    now_kst = datetime.now(KST)
    today = now_kst.strftime("%Y-%m-%d")

    seen, all_games = set(), []
    sample_holder = {"sample": None}
    d = SEASON_START
    while d <= now_kst.date() + timedelta(days=6):
        url = f"https://mykbostats.com/schedule/week_of/{d.isoformat()}"
        try:
            html = fetch(url)
        except Exception as exc:
            print(f"  week {d} failed: {exc}")
            d += timedelta(days=7)
            continue
        for g in parse_week(html, today, sample_holder):
            key = (g["date"], g["away"], g["home"])
            if key not in seen:
                seen.add(key)
                all_games.append(g)
        time.sleep(0.15)
        d += timedelta(days=7)

    finals = [g for g in all_games if g["status"] == "final"]
    print(f"KBO: crawled {len(all_games)} games; parsed {len(finals)} finals")
    if sample_holder["sample"]:
        print(f'  [verify-scores] sample past game-line text: {sample_holder["sample"]!r}')
    if not finals:
        print("KBO: no finals parsed — score markup differs from the conservative "
              "pattern; team stats/H2H honestly omitted. Send this log for a follow-up.")

    stats = team_form(finals) if finals else {}
    todays = [g for g in all_games if g["date"] == today]

    games_out = []
    for g in todays:
        entry = {
            "away": g["away"], "home": g["home"], "stadium": g["stadium"],
            "time_kst": g["time_kst"], "time_et": g["time_et"],
            "away_starter": "TBD", "home_starter": "TBD",
            "status": g["status"],
        }
        for side in ("away", "home"):
            s = stats.get(g[side])
            if s:
                entry[f"{side}_record"] = s["record"]
                entry[f"{side}_rs_pg"] = s["rs_pg"]
                entry[f"{side}_ra_pg"] = s["ra_pg"]
                entry[f"{side}_last10"] = s["last10"]
        hh = h2h(finals, g["away"], g["home"]) if finals else None
        if hh:
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
    (OUT / "games.json").write_text(json.dumps({
        "generated_at_kst": now_kst.strftime("%Y-%m-%d %H:%M"),
        "source": "mykbostats.com schedule (season crawl)",
        "slate_date_kst": today,
        "games": games_out,
    }, ensure_ascii=False, indent=2))
    print(f"KBO: wrote {len(games_out)} games for {today} KST")
    if not games_out:
        print("KBO: empty slate — off-day or break. That is the honest state.")


if __name__ == "__main__":
    main()