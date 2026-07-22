"""
Calibration — did the picks actually hit?

This is the honesty backstop for every score on the site. Impressions
lie: on a 15-game slate roughly 25 home runs happen, so any list of
high-barrel bats in good parks will "look right" some nights. The only
way to know whether HR Edge, the Daily 13, or anyone else's picks
beat a coin flip is to write down the picks BEFORE the games and
grade them AFTER.

How it works:
  - log_picks(board, date, rows) writes that day's top picks to a
    local JSON file, once per board per day (re-running is idempotent
    — it overwrites the same day's entry rather than duplicating).
  - grade_pending() looks up every logged pick from a past date and
    fills in what actually happened, from MLB's official box-score
    game logs (the same source the trend charts use).
  - summary() reports hit rate by board over the tracked period.

What's graded per board:
  daily13  -> did the batter get >= 1 hit that day
  hr_edge  -> did the batter hit >= 1 home run that day

Storage is a plain JSON file under the app's data directory. It's
small (a few KB per week), survives redeploys only if the data volume
does — so this is a rolling record, and the page says so rather than
implying a permanent ledger.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import streamlit as st

EASTERN = ZoneInfo("America/New_York")
_LOG_PATH = Path(__file__).resolve().parents[1] / "data" / "calibration.json"
_URL = "https://statsapi.mlb.com/api/v1/people/{pid}/stats"

BOARDS = {
    "daily13": {"label": "Daily 13", "stat": "hits", "threshold": 1,
                "question": "got a hit"},
    "hr_edge": {"label": "HR Edge (top 5)", "stat": "homeRuns", "threshold": 1,
                "question": "hit a home run"},
}


def _load():
    try:
        return json.loads(_LOG_PATH.read_text())
    except Exception:
        return {}


def _save(data):
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _LOG_PATH.write_text(json.dumps(data, indent=2))
        return True
    except Exception:
        return False


def log_picks(board: str, rows, date_str: str = None) -> bool:
    """Record today's picks for later grading. rows: [{"id","name",
    "team"}...]. Idempotent per (board, date)."""
    if board not in BOARDS or not rows:
        return False
    date_str = date_str or datetime.now(EASTERN).strftime("%Y-%m-%d")
    data = _load()
    data.setdefault(board, {})
    data[board][date_str] = {
        "picks": [{"id": r.get("id"), "name": r.get("name"),
                   "team": r.get("team"), "result": None}
                  for r in rows if r.get("id")],
        "graded": False,
    }
    return _save(data)


@st.cache_data(ttl=3600, max_entries=256, show_spinner=False)
def _player_day_json(pid: int, date_str: str, season: int) -> str:
    """That player's official box-score line for one date."""
    try:
        resp = requests.get(
            _URL.format(pid=pid),
            params={"stats": "gameLog", "group": "hitting", "season": season},
            timeout=10,
        )
        resp.raise_for_status()
        stats = resp.json().get("stats") or []
        splits = (stats[0].get("splits") if stats else []) or []
    except Exception:
        return json.dumps(None)
    for sp in splits:
        if sp.get("date") == date_str:
            stat = sp.get("stat", {}) or {}
            try:
                return json.dumps({"hits": int(stat.get("hits", 0)),
                                   "homeRuns": int(stat.get("homeRuns", 0))})
            except Exception:
                return json.dumps(None)
    return json.dumps(None)


def grade_pending(max_days: int = 14) -> int:
    """Fill in outcomes for logged picks from past dates. Returns the
    number of newly graded picks. Only grades dates strictly before
    today, so an in-progress slate is never scored."""
    data = _load()
    today = datetime.now(EASTERN).strftime("%Y-%m-%d")
    cutoff = (datetime.now(EASTERN) - timedelta(days=max_days)).strftime("%Y-%m-%d")
    graded_n = 0
    for board, days in data.items():
        cfg = BOARDS.get(board)
        if not cfg:
            continue
        for date_str, entry in days.items():
            if entry.get("graded") or date_str >= today or date_str < cutoff:
                continue
            season = int(date_str[:4])
            all_done = True
            for pick in entry.get("picks", []):
                if pick.get("result") is not None or not pick.get("id"):
                    continue
                try:
                    line = json.loads(_player_day_json(int(pick["id"]), date_str, season))
                except Exception:
                    line = None
                if line is None:
                    # didn't play, or the log isn't available — mark it
                    # DNP rather than counting it as a miss
                    pick["result"] = "dnp"
                else:
                    pick["result"] = ("hit" if line.get(cfg["stat"], 0) >= cfg["threshold"]
                                      else "miss")
                    graded_n += 1
            entry["graded"] = all_done
    if graded_n:
        _save(data)
    return graded_n


def summary():
    """Per-board record over everything graded so far."""
    data = _load()
    out = {}
    for board, cfg in BOARDS.items():
        days = data.get(board, {})
        hits = misses = dnp = 0
        dates = []
        for date_str, entry in sorted(days.items()):
            day_hits = sum(1 for p in entry.get("picks", []) if p.get("result") == "hit")
            day_miss = sum(1 for p in entry.get("picks", []) if p.get("result") == "miss")
            day_dnp = sum(1 for p in entry.get("picks", []) if p.get("result") == "dnp")
            if day_hits or day_miss:
                dates.append({"date": date_str, "hits": day_hits,
                              "total": day_hits + day_miss})
            hits += day_hits
            misses += day_miss
            dnp += day_dnp
        total = hits + misses
        out[board] = {
            "label": cfg["label"], "question": cfg["question"],
            "hits": hits, "total": total, "dnp": dnp,
            "rate": round(hits / total * 100, 1) if total else None,
            "days": dates,
        }
    return out
