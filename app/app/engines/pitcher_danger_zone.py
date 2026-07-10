import pandas as pd
import numpy as np

def build_pitcher_danger_zone(pitcher_profile):
    """
    Crash-proof pitcher danger zone generator.
    Uses safe .get() calls so missing stats never break the app.
    """

    # SAFE GETS — no KeyErrors ever
    hr_rate = pitcher_profile.get("HR/BBE", 0)
    hh = pitcher_profile.get("HH %", 0)
    ld = pitcher_profile.get("LD %", 0)
    brl = pitcher_profile.get("Brl %", 0)
    zone_contact = pitcher_profile.get("ZoneContact %", 0)

    # Vulnerability scoring model
    vuln_score = (
        (hr_rate * 0.35) +
        (hh * 0.25) +
        (ld * 0.20) +
        (brl * 0.15) +
        (zone_contact * 0.05)
    )

    # Build 3x3 grid
    grid = np.array([
        [vuln_score * 1.0, vuln_score * 0.8, vuln_score * 0.6],
        [vuln_score * 0.9, vuln_score * 0.7, vuln_score * 0.5],
        [vuln_score * 0.8, vuln_score * 0.6, vuln_score * 0.4]
    ])

    df = pd.DataFrame(
        grid,
        columns=["Inside", "Middle", "Outside"],
        index=["High", "Mid", "Low"]
    )

    return df
