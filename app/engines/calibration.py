"""
Calibration (app side) — READ ONLY.

The record itself is produced by the nightly pipeline (see
calibration_pipeline.py and slate_picks.py at the repo root) and
ships inside the data package. The app never writes it: the app's
data directory is rebuilt on every deploy, so anything written here
would be erased within hours.

This module just reads what the pipeline published.
"""
import json
from pathlib import Path

import streamlit as st

_RECORD = Path(__file__).resolve().parents[1] / "data" / "statcast" / "calibration.json"

BOARDS = {
    "daily13": {"label": "Daily 13", "question": "got a hit"},
    "hr_edge": {"label": "HR Edge (slate top 10)", "question": "hit a home run"},
}


@st.cache_data(ttl=1800, show_spinner=False)
def _load_json() -> str:
    try:
        return _RECORD.read_text()
    except Exception:
        return "{}"


def summary():
    """Per-board record, or empty dict when nothing is tracked yet."""
    try:
        data = json.loads(_load_json())
    except Exception:
        data = {}
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
                per_day.append({"date": date_str, "hits": d_hit,
                                "total": d_hit + d_miss,
                                "picks": entry.get("picks", [])})
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


def board_record(board: str):
    """One board's summary, or None when untracked."""
    s = summary().get(board)
    return s if s and s.get("total") else None
