"""
Calibration (pipeline side) — the honest scorecard.

Runs inside the nightly data build, not the app. Two jobs each night:

  1. GRADE  — look up every previously logged pick whose games are
              final and record whether it hit, using MLB's official
              box-score game logs.
  2. LOG    — compute tonight's slate-wide top picks the same way
              every night and write them down BEFORE the games.

Why pipeline-side rather than in the app: the app's data directory is
rebuilt on every deploy, so anything it writes is erased within hours.
The record lives inside the same data package the pipeline publishes,
so it survives deploys and travels with the rest of the data.

Why slate-wide rather than per-page: a record is only meaningful if
the picks are chosen the same way every night. Logging whatever bats a
user happened to have on screen would measure the user's clicking, not
the model.

What's tracked:
  daily13  -> the Daily 13 board's picks; did each get >= 1 hit
  hr_edge  -> the slate's top HR Edge bats; did each hit >= 1 HR

The record is a rolling window (default 45 days) so the file stays
small and the reported rate reflects the model as it currently is,
not a version from months ago.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

EASTERN = ZoneInfo("America/New_York")
_STATS_URL = "https://statsapi.mlb.com/api/v1/people/{pid}/stats"
_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"

RETENTION_DAYS = 45
HR_EDGE_PICKS = 10   # slate-wide top N logged per night

BOARDS = {
    "daily13": {"label": "Daily 13", "stat": "hits", "threshold": 1,
                "question": "got a hit"},
    "hr_edge": {"label": "HR Edge (slate top 10)", "stat": "homeRuns",
                "threshold": 1, "question": "hit a home run"},
}


def _load(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save(path: Path, data) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        return True
    except Exception as exc:
        print(f"[calibration] WARNING: could not write record ({exc})")
        return False


def _player_day(pid: int, date_str: str):
    """Official box-score line for one player on one date, or None if
    he didn't appear."""
    season = int(date_str[:4])
    try:
        resp = requests.get(
            _STATS_URL.format(pid=pid),
            params={"stats": "gameLog", "group": "hitting", "season": season},
            timeout=15,
        )
        resp.raise_for_status()
        stats = resp.json().get("stats") or []
        splits = (stats[0].get("splits") if stats else []) or []
    except Exception:
        return None
    for sp in splits:
        if sp.get("date") == date_str:
            stat = sp.get("stat", {}) or {}
            try:
                return {"hits": int(stat.get("hits", 0)),
                        "homeRuns": int(stat.get("homeRuns", 0))}
            except Exception:
                return None
    return None


def _slate_is_final(date_str: str) -> bool:
    """True when every game that date has finished — so a slate is
    never graded while games are still being played."""
    try:
        resp = requests.get(
            _SCHEDULE_URL,
            params={"sportId": 1, "date": date_str},
            timeout=15,
        )
        resp.raise_for_status()
        dates = resp.json().get("dates") or []
    except Exception:
        return False
    if not dates:
        return False
    for d in dates:
        for g in d.get("games", []):
            state = ((g.get("status") or {}).get("abstractGameState") or "").lower()
            if state not in ("final", "completed"):
                return False
    return True


def grade(record_path: Path) -> int:
    """Fill in outcomes for logged picks whose slates are complete.
    Returns the number newly graded."""
    data = _load(record_path)
    today = datetime.now(EASTERN).strftime("%Y-%m-%d")
    graded_n = 0
    for board, days in data.items():
        cfg = BOARDS.get(board)
        if not cfg:
            continue
        for date_str, entry in sorted(days.items()):
            if entry.get("graded") or date_str >= today:
                continue
            if not _slate_is_final(date_str):
                print(f"[calibration] {date_str} not final yet — leaving ungraded")
                continue
            for pick in entry.get("picks", []):
                if pick.get("result") is not None or not pick.get("id"):
                    continue
                line = _player_day(int(pick["id"]), date_str)
                if line is None:
                    # Didn't play. Not a miss — a pick that never got a
                    # plate appearance says nothing about the model.
                    pick["result"] = "dnp"
                else:
                    pick["result"] = ("hit" if line.get(cfg["stat"], 0) >= cfg["threshold"]
                                      else "miss")
                    graded_n += 1
            entry["graded"] = True
            hits = sum(1 for p in entry["picks"] if p.get("result") == "hit")
            total = sum(1 for p in entry["picks"] if p.get("result") in ("hit", "miss"))
            print(f"[calibration] graded {board} {date_str}: {hits}/{total}")
    if graded_n:
        _save(record_path, data)
    return graded_n


def log(record_path: Path, board: str, picks, date_str: str = None) -> bool:
    """Write tonight's picks. picks: [{"id","name","team"}...].
    Idempotent per (board, date) — re-running the pipeline the same day
    overwrites rather than duplicating."""
    if board not in BOARDS or not picks:
        return False
    date_str = date_str or datetime.now(EASTERN).strftime("%Y-%m-%d")
    data = _load(record_path)
    data.setdefault(board, {})
    if data[board].get(date_str, {}).get("graded"):
        # never overwrite a graded day
        return False
    data[board][date_str] = {
        "picks": [{"id": p.get("id"), "name": p.get("name"),
                   "team": p.get("team"), "result": None}
                  for p in picks if p.get("id")],
        "graded": False,
    }
    print(f"[calibration] logged {board} {date_str}: {len(data[board][date_str]['picks'])} picks")
    return _save(record_path, data)


def prune(record_path: Path) -> None:
    """Drop entries older than the retention window."""
    data = _load(record_path)
    cutoff = (datetime.now(EASTERN) - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d")
    changed = False
    for board, days in data.items():
        for date_str in list(days.keys()):
            if date_str < cutoff:
                del days[date_str]
                changed = True
    if changed:
        _save(record_path, data)


def summarize(record_path: Path):
    """Per-board record over everything graded."""
    data = _load(record_path)
    out = {}
    for board, cfg in BOARDS.items():
        days = data.get(board, {})
        hits = misses = dnp = 0
        per_day = []
        for date_str, entry in sorted(days.items()):
            d_hit = sum(1 for p in entry.get("picks", []) if p.get("result") == "hit")
            d_miss = sum(1 for p in entry.get("picks", []) if p.get("result") == "miss")
            d_dnp = sum(1 for p in entry.get("picks", []) if p.get("result") == "dnp")
            if d_hit or d_miss:
                per_day.append({"date": date_str, "hits": d_hit, "total": d_hit + d_miss})
            hits += d_hit
            misses += d_miss
            dnp += d_dnp
        total = hits + misses
        out[board] = {
            "label": cfg["label"], "question": cfg["question"],
            "hits": hits, "total": total, "dnp": dnp,
            "rate": round(hits / total * 100, 1) if total else None,
            "days": per_day,
        }
    return out
