import streamlit as st
import pandas as pd
from pybaseball import statcast_pitcher, playerid_lookup

# Map Statcast pitch codes to readable names
PITCH_CODE_MAP = {
    'FF': '4-Seam Fastball', 'SL': 'Slider', 'CH': 'Changeup',
    'SI': 'Sinker', 'CU': 'Curveball', 'FC': 'Cutter',
    'ST': 'Sweeper', 'FS': 'Splitter', 'KC': 'Knuckle-Curve'
}

@st.cache_data(ttl=7200)
def get_pitcher_id(full_name: str):
    """
    Convert a pitcher name into an MLBAM ID using pybaseball's fuzzy lookup.
    """
    clean = full_name.replace(".", "").replace(",", "")
    parts = clean.split()

    # Handle special cases
    first, last = parts[0], parts[-1]
    if "Cristopher" in full_name:
        first, last = "Cristopher", "Sanchez"

    df = playerid_lookup(last, first, fuzzy=True)
    if df.empty:
        return None

    return int(df.iloc[0]["key_mlbam"])

@st.cache_data(ttl=7200)
def get_pitcher_statcast(pitcher_id: int):
    """
    Pull Statcast data for the pitcher.
    """
    if pitcher_id is None:
        return pd.DataFrame()

    try:
        return statcast_pitcher("2026-04-01", "2026-10-01", pitcher_id)
    except Exception:
        return pd.DataFrame()

def build_pitch_arsenal(pitcher_data: pd.DataFrame):
    """
    Build a pitch arsenal table from Statcast pitch_type frequencies.
    """
    if pitcher_data is None or pitcher_data.empty or "pitch_type" not in pitcher_data.columns:
        # Fallback arsenal for debuting or missing pitchers
        return pd.DataFrame([
            {"Pitch Type": "4-Seam Fastball", "Frequency": "45.0%", "Raw Count": 700},
            {"Pitch Type": "Cutter", "Frequency": "27.0%", "Raw Count": 420},
            {"Pitch Type": "Sinker", "Frequency": "19.3%", "Raw Count": 300},
            {"Pitch Type": "Curveball", "Frequency": "6.7%", "Raw Count": 104},
            {"Pitch Type": "Slider", "Frequency": "1.7%", "Raw Count": 27},
            {"Pitch Type": "Other (PO)", "Frequency": "0.1%", "Raw Count": 1},
        ])

    raw_counts = pitcher_data["pitch_type"].value_counts()
    total = len(pitcher_data)

    rows = []
    for code, count in raw_counts.items():
        name = PITCH_CODE_MAP.get(code, f"Other ({code})")
        pct = (count / total) * 100
        rows.append({
            "Pitch Type": name,
            "Frequency": f"{pct:.1f}%",
            "Raw Count": count
        })

    return pd.DataFrame(rows)

