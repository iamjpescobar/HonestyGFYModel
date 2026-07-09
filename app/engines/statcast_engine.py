import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher


# ============================================================
# SAFE STATCAST ENGINE (BATTER + PITCHER IN ONE FILE)
# ============================================================

def _safe_statcast_pull(func, player_id):
    """
    Safest possible Statcast pull wrapper.
    Prevents crashes, returns empty DataFrame if needed.
    """
    try:
        df = func(player_id)
        if df is None or len(df) == 0:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


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
