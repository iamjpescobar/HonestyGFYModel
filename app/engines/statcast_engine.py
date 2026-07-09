import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher, playerid_lookup

DEFAULT_START_DATE = "2026-03-01"
DEFAULT_END_DATE = "2026-11-01"


# ============================================================
# SAFE STATCAST ENGINE (BATTER + PITCHER IN ONE FILE)
# ============================================================

def _safe_statcast_pull(func, player_id, start_date=DEFAULT_START_DATE, end_date=DEFAULT_END_DATE):
    """
    Safest possible Statcast pull wrapper.
    Prevents crashes, returns empty DataFrame if needed.
    """
    try:
        df = func(start_date, end_date, player_id)
        if df is None or len(df) == 0:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def get_pitcher_id(full_name: str):
    """
    Resolves a player's full name (e.g. "Gerrit Cole") to an MLBAM id
    using pybaseball's player lookup. Returns None if no match is found
    so callers can fail safely instead of crashing.
    """
    if not full_name or not isinstance(full_name, str):
        return None

    parts = full_name.strip().split(" ")
    if len(parts) < 2:
        return None

    first_name = parts[0]
    last_name = " ".join(parts[1:])

    try:
        matches = playerid_lookup(last_name, first_name)
        if matches is None or matches.empty:
            return None
        # Most recent player if multiple people share the name
        matches = matches.sort_values("mlb_played_last", ascending=False)
        return int(matches.iloc[0]["key_mlbam"])
    except Exception:
        return None


def build_pitch_arsenal(pitcher_data: dict) -> pd.DataFrame:
    """
    Converts the 'Pitch Arsenal' usage dict inside a pitcher profile
    (as returned by get_pitcher_statcast) into a clean DataFrame for display.
    """
    arsenal = {}
    if isinstance(pitcher_data, dict):
        arsenal = pitcher_data.get("Pitch Arsenal", {}) or {}

    if not arsenal:
        return pd.DataFrame(columns=["Pitch Type", "Usage %"])

    df = pd.DataFrame(
        list(arsenal.items()),
        columns=["Pitch Type", "Usage %"]
    ).sort_values("Usage %", ascending=False).reset_index(drop=True)

    return df


# ============================================================
# BATTER STATCAST PROFILE
# ============================================================

def get_batter_statcast(batter_id):
    df = _safe_statcast_pull(statcast_batter, batter_id)

    profile = {}

    if df.empty:
        # Safe fallback profile
        return {
            "Brl %": 0,
            "HH %": 0,
            "PullAir %": 0,
            "LD %": 0,
            "GB %": 0,
            "Whiff %": 0,
            "BBE": 0
        }

    # -----------------------------
    # Core Statcast Metrics
    # -----------------------------
    profile["Brl %"] = round(df.get("barrel", pd.Series([0])).mean() * 100, 2)
    profile["HH %"] = round(df.get("hard_hit", pd.Series([0])).mean() * 100, 2)
    profile["PullAir %"] = round(df.get("pull_air", pd.Series([0])).mean() * 100, 2)
    profile["LD %"] = round(df.get("ld", pd.Series([0])).mean() * 100, 2)
    profile["GB %"] = round(df.get("gb", pd.Series([0])).mean() * 100, 2)

    # -----------------------------
    # Whiff % (Swinging Strikes)
    # -----------------------------
    if "description" in df.columns:
        whiff = (df["description"].str.contains("swinging_strike")).mean() * 100
    else:
        whiff = 0

    profile["Whiff %"] = round(whiff, 2)

    # -----------------------------
    # Sample Size
    # -----------------------------
    profile["BBE"] = len(df)

    return profile


# ============================================================
# PITCHER STATCAST PROFILE
# ============================================================

def get_pitcher_statcast(pitcher_id):
    df = _safe_statcast_pull(statcast_pitcher, pitcher_id)

    profile = {}

    if df.empty:
        return {
            "HR/BBE": 0,
            "HH %": 0,
            "LD %": 0,
            "Brl %": 0,
            "ZoneContact %": 0,
            "Whiff %": 0,
            "Pitch Arsenal": {},
            "BBE": 0
        }

    # -----------------------------
    # Core Pitcher Metrics
    # -----------------------------
    profile["HR/BBE"] = round(df.get("hr", pd.Series([0])).mean(), 3)
    profile["HH %"] = round(df.get("hard_hit", pd.Series([0])).mean() * 100, 2)
    profile["LD %"] = round(df.get("ld", pd.Series([0])).mean() * 100, 2)
    profile["Brl %"] = round(df.get("barrel", pd.Series([0])).mean() * 100, 2)
    profile["ZoneContact %"] = round(df.get("zone_contact", pd.Series([0])).mean() * 100, 2)

    # -----------------------------
    # Whiff % (Swinging Strikes)
    # -----------------------------
    if "description" in df.columns:
        whiff = (df["description"].str.contains("swinging_strike")).mean() * 100
    else:
        whiff = 0

    profile["Whiff %"] = round(whiff, 2)

    # -----------------------------
    # Pitch Arsenal (safe)
    # -----------------------------
    if "pitch_type" in df.columns:
        arsenal = df["pitch_type"].value_counts(normalize=True) * 100
        profile["Pitch Arsenal"] = {k: round(v, 2) for k, v in arsenal.items()}
    else:
        profile["Pitch Arsenal"] = {}

    # -----------------------------
    # Sample Size
    # -----------------------------
    profile["BBE"] = len(df)

    return profile
