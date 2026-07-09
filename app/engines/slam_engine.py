import pandas as pd
from pybaseball import statcast_pitcher, statcast_batter

# Pitch code → readable pitch name
PITCH_MAP = {
    "FF": "4-Seam Fastball",
    "FT": "2-Seam Fastball",
    "SI": "Sinker",
    "SL": "Slider",
    "CH": "Changeup",
    "CU": "Curveball",
    "KC": "Knuckle Curve",
    "FS": "Splitter",
    "FC": "Cutter",
    "ST": "Sweeper",
}

def get_pitcher_statcast(mlbam_id, start_date="2024-03-01", end_date="2024-11-01"):
    """
    Returns a SAFE pitcher profile with all fields needed by:
    - pitcher danger zone
    - matchup engine
    - KC page
    """

    try:
        df = statcast_pitcher(start_date, end_date, mlbam_id)
    except Exception:
        return {
            "HR/BBE": 0,
            "HH %": 0,
            "LD %": 0,
            "Brl %": 0,
            "ZoneContact %": 0,
            "Pitch Arsenal": {},
        }

    if df.empty:
        return {
            "HR/BBE": 0,
            "HH %": 0,
            "LD %": 0,
            "Brl %": 0,
            "ZoneContact %": 0,
            "Pitch Arsenal": {},
        }

    # Hard Hit %
    hh = (df["launch_speed"] >= 95).mean() * 100

    # Barrel %
    brl = df["barrel"].mean() * 100 if "barrel" in df.columns else 0

    # Line Drive %
    ld = (df["bb_type"] == "line_drive").mean() * 100

    # HR / BBE
    hr_bbe = (df["events"] == "home_run").sum() / len(df) * 100

    # Zone Contact %
    if "zone" in df.columns and "contact" in df.columns:
        zone_df = df[df["zone"].notna()]
        zone_contact = (zone_df["contact"] == 1).mean() * 100 if not zone_df.empty else 0
    else:
        zone_contact = 0

    # Pitch Arsenal
    arsenal = (
        df.groupby("pitch_type")
        .size()
        .sort_values(ascending=False)
        .to_dict()
    )

    readable_arsenal = {
        PITCH_MAP.get(k, k): v for k, v in arsenal.items()
    }

    return {
        "HR/BBE": round(hr_bbe, 2),
        "HH %": round(hh, 2),
        "LD %": round(ld, 2),
        "Brl %": round(brl, 2),
        "ZoneContact %": round(zone_contact, 2),
        "Pitch Arsenal": readable_arsenal,
    }


def get_batter_statcast(mlbam_id, start_date="2024-03-01", end_date="2024-11-01"):
    """
    Returns SAFE batter Statcast profile for:
    - batter danger zone
    - matchup engine
    - KC page
    """

    try:
        df = statcast_batter(start_date, end_date, mlbam_id)
    except Exception:
        return {
            "Brl %": 0,
            "HH %": 0,
            "PullAir %": 0,
            "LD %": 0,
        }

    if df.empty:
        return {
            "Brl %": 0,
            "HH %": 0,
            "PullAir %": 0,
            "LD %": 0,
        }

    brl = df["barrel"].mean() * 100 if "barrel" in df.columns else 0
    hh = (df["launch_speed"] >= 95).mean() * 100
    ld = (df["bb_type"] == "line_drive").mean() * 100

    # Pull Air %
    pull_air = (
        ((df["hc_x"] < 125) & (df["launch_angle"] > 10)).mean() * 100
        if "hc_x" in df.columns and "launch_angle" in df.columns
        else 0
    )

    return {
        "Brl %": round(brl, 2),
        "HH %": round(hh, 2),
        "PullAir %": round(pull_air, 2),
        "LD %": round(ld, 2),
    }
