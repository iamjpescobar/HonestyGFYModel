import numpy as np

def compute_matchup_multiplier(batter_profile: dict, pitcher_profile: dict):
    """
    Data-driven matchup engine:
    - Compares batter strengths vs pitcher weaknesses
    - Returns:
        matchup_mult (float)
        matchup_tag (str)
    """

    # Batter strengths
    brl = batter_profile["Brl %"]
    hh = batter_profile["HH %"]
    pull_air = batter_profile["PullAir %"]
    ld = batter_profile["LD %"]

    # Pitcher weaknesses
    hr_bbe = pitcher_profile["HR/BBE"]
    hh_allowed = pitcher_profile["HH Allowed %"]
    ld_allowed = pitcher_profile["LD Allowed %"]
    zone_vuln = pitcher_profile["ZoneVuln Score"]  # from pitcher danger zone

    # Batter damage score
    score = (
        (brl * 0.40) +
        (hh * 0.25) +
        (pull_air * 0.20) +
        (ld * 0.15)
    )

    # Pitcher vulnerability score
    vuln = (
        (hr_bbe * 0.45) +
        (hh_allowed * 0.30) +
        (ld_allowed * 0.15) +
        (zone_vuln * 0.10)
    )

    raw = score * (1.0 + (vuln / 100.0))

    # Convert to multiplier + tag
    if raw >= 80:
        matchup_mult = 1.20
        matchup_tag = "ELITE"
    elif raw >= 65:
        matchup_mult = 1.10
        matchup_tag = "GOOD"
    elif raw >= 50:
        matchup_mult = 1.00
        matchup_tag = "Neutral"
    elif raw >= 35:
        matchup_mult = 0.90
        matchup_tag = "Cold"
    else:
        matchup_mult = 0.80
        matchup_tag = "⚠️"

    return float(matchup_mult), matchup_tag
