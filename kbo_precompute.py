"""
KBO slate + season data fetcher — real data from MyKBOStats, plus real
season pitching lines from the official KBO stats site.

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

v3 fixes a confirmed bug: MyKBOStats renders finished-game scores as
"5 : 0" (colon-separated), but the score pattern below was written to
match "5-0" (dash) and explicitly excluded colons to avoid confusing a
score with a start time — so it could never match a real final, and
team stats/H2H always shipped empty. Verified directly against live
site output before this fix. v3 also adds a real pitching leaderboard
pulled from the official KBO site (eng.koreabaseball.com), the same
standard as the NPB engine: league-maintained arithmetic, nothing
modeled. (Pre-game probable starters are not present in either source's
static HTML at fetch time, so starters continue to ship honestly as
TBD rather than guessed — same as before.)
"""

import json
import re
import time
from datetime import date, datetime, timedelta
from io import StringIO
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
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

# Keyed only on the href, which has stayed stable across the site's
# v2 -> v3 rebuild (verified against both live), rather than the
# specific id/class attributes on the <a>, which are more likely to
# drift with a front-end refresh.
GAME_LINE = re.compile(
    r'<a[^>]*href="/games/\d+-([A-Za-z]+)-vs-([A-Za-z]+)-(\d{8})"[^>]*>(.*?)</a>',
    re.S,
)
# Real finished-game score format, verified live: "5 : 0" (colon, with
# spaces) immediately followed by a "Final" status word in the same
# game-line — e.g. "Hanwha Eagles 5 : 0 Final KT Wiz". Requiring the
# "final" keyword alongside the number pair (checked in parse_week)
# keeps this from ever mistaking a start time like "6:30pm" for a score.
SCORE_PAT = re.compile(r'(?<![\d.:])(\d{1,2})\s*:\s*(\d{1,2})(?!\s*[ap]m)(?!\d)', re.I)
POSTPONED_PAT = re.compile(r'postponed|cancell?ed', re.I)
FINAL_PAT = re.compile(r'final', re.I)


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
            if FINAL_PAT.search(text):
                sm = SCORE_PAT.search(text)
                if sm:
                    # Away is listed first on the page, so away-home order.
                    g["away_score"], g["home_score"] = int(sm.group(1)), int(sm.group(2))
                    g["status"] = "final"
            elif POSTPONED_PAT.search(text):
                g["status"] = "postponed"
        yield g


KBO_TEAM_CODE = {
    "SAMSUNG": "Samsung Lions", "KIA": "Kia Tigers", "KT": "KT Wiz",
    "LG": "LG Twins", "HANWHA": "Hanwha Eagles", "LOTTE": "Lotte Giants",
    "DOOSAN": "Doosan Bears", "KIWOOM": "Kiwoom Heroes", "NC": "NC Dinos",
    "SSG": "SSG Landers",
}

# Official KBO leaderboard, split across two pages (basic + detailed
# columns) that together give a full real season line per pitcher.
# Verified live: page1 has RK/PLAYER/TEAM/ERA/G/CG/SHO/W/L/SV/HLD/PCT/
# PA/NP/IP/H/2B/3B/HR; page2 has RK/PLAYER/TEAM/SAC/SF/BB/IBB/HBP/SO/
# WP/BK/R/ER/BS/WHIP/OAVG/QS.
PITCHING_LEADER_URLS = (
    "https://eng.koreabaseball.com/Stats/PitchingLeaders.aspx",
    "https://eng.koreabaseball.com/Stats/PitchingLeaders02.aspx",
)


def fetch_pitcher_stats():
    """Real season pitching lines for the KBO's most-used arms, straight
    from the league's own official leaderboard — the same standard as
    the NPB engine: real box-score arithmetic KBO itself maintains,
    nothing modeled or estimated.

    Uses pandas.read_html against the actual <table> markup rather than
    a hand-written regex, since the exact CSS classes on this ASP.NET
    site weren't available to verify offline — reading the real table
    structure directly is more robust than guessing selectors.

    Wrapped so a site hiccup or markup change degrades to an empty dict
    rather than failing the whole KBO build — the slate itself must
    still ship even if pitcher stats can't be fetched.
    """
    tables = []
    for url in PITCHING_LEADER_URLS:
        try:
            r = requests.get(url, headers=UA, timeout=25)
            r.raise_for_status()
            page_tables = pd.read_html(StringIO(r.text))
        except Exception as exc:
            print(f"  KBO pitching leaders fetch failed for {url}: {exc}")
            continue
        if not page_tables:
            continue
        # The stats grid is by far the largest table on the page.
        page_tables.sort(key=len, reverse=True)
        tables.append(page_tables[0])

    if not tables:
        return {}

    df = tables[0]
    for extra in tables[1:]:
        if "PLAYER" not in extra.columns or "TEAM" not in extra.columns:
            continue
        df = df.merge(extra, on=["PLAYER", "TEAM"], how="outer", suffixes=("", "_dup"))

    def _val(row, col):
        v = row.get(col)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if hasattr(v, "item"):  # numpy scalar (int64/float64) -> plain Python
            v = v.item()
        return v

    stats = {}
    for _, row in df.iterrows():
        name = str(row.get("PLAYER", "")).strip()
        team_code = str(row.get("TEAM", "")).strip()
        if not name or name.lower() == "nan":
            continue
        stats[name] = {
            "team": KBO_TEAM_CODE.get(team_code, team_code),
            "era": _val(row, "ERA"),
            "games": _val(row, "G"),
            "wins": _val(row, "W"),
            "losses": _val(row, "L"),
            "saves": _val(row, "SV"),
            "holds": _val(row, "HLD"),
            "innings_pitched": _val(row, "IP"),
            "strikeouts": _val(row, "SO"),
            "walks": _val(row, "BB"),
            "whip": _val(row, "WHIP"),
            "quality_starts": _val(row, "QS"),
            "runs_allowed": _val(row, "R"),
            "earned_runs": _val(row, "ER"),
        }
    return stats


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

    try:
        pitcher_stats = fetch_pitcher_stats()
    except Exception as exc:
        pitcher_stats = {}
        print(f"KBO: pitcher-stats fetch failed ({exc}) — shipping without it")
    print(f"KBO: {len(pitcher_stats)} pitchers with real season stats fetched "
          f"from the official KBO leaderboard")

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

    # Sorted by ERA (qualified arms only, i.e. everyone the leaderboard
    # itself lists) so the page can show it as a straight leaderboard.
    def _era_key(p):
        try:
            return float(p["era"])
        except (TypeError, ValueError):
            return float("inf")

    leaders_out = sorted(
        ({"name": name, **info} for name, info in pitcher_stats.items()
         if info.get("era") is not None),
        key=_era_key,
    )
    (OUT / "pitchers.json").write_text(json.dumps({
        "generated_at_kst": now_kst.strftime("%Y-%m-%d %H:%M"),
        "source": "eng.koreabaseball.com official pitching leaderboard",
        "pitchers": leaders_out,
    }, ensure_ascii=False, indent=2))
    print(f"KBO: wrote {len(leaders_out)} pitchers to pitchers.json")
    if not leaders_out:
        print("KBO: no pitcher stats parsed — official leaderboard markup may "
              "have changed; page will honestly omit the pitching section.")
    print("KBO: probable starters are not present in either source's static "
          "HTML at fetch time, so starters continue to ship as TBD rather "
          "than guessed.")


if __name__ == "__main__":
    main()