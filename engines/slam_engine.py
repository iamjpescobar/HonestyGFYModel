import numpy as np

def random_match_tag(batter_name: str) -> str:
    np.random.seed(abs(hash(batter_name)) % (10**8))
    return np.random.choice(
        ["🔥 ELITE", "✅ Good", "Neutral", "⚠️ Cold"],
        p=[0.15, 0.45, 0.30, 0.10]
    )

def compute_slam_index(
    brl: float,
    hh: float,
    pull_air: float,
    gb: float,
    bbe: int,
    matchup_tag: str,
    affinity_mult: float = 1.0
) -> float:
    base_score = (brl * 3.5) + (hh * 0.5) + (pull_air * 0.3) - (gb * 0.2)

    if matchup_tag == "✅ Good":
        base_score *= 1.15
    if matchup_tag == "🔥 ELITE":
        base_score *= 1.25

    if bbe > 120:
        base_score += 8

    base_score *= affinity_mult

    return float(min(100.0, max(5.0, base_score)))

def compute_matchup_affinity(pitcher_arsenal, batter_profile):
    if pitcher_arsenal is None or pitcher_arsenal.empty:
        return 1.0

    usage = pitcher_arsenal.set_index("Pitch Type")["Raw Count"]
    usage_pct = usage / usage.sum()

    brl = batter_profile["Brl %"]
    hh = batter_profile["HH %"]
    pull = batter_profile["PullAir %"]
    gb = batter_profile["GB %"]
    ld = batter_profile["LD %"]

    affinity = 1.0

    if "4-Seam Fastball" in usage_pct.index and usage_pct["4-Seam Fastball"] > 0.35:
        if brl > 10:
            affinity += 0.10

    if "Slider" in usage_pct.index and usage_pct["Slider"] > 0.25:
        if gb > 45:
            affinity -= 0.08

    if "Curveball" in usage_pct.index and usage_pct["Curveball"] > 0.20:
        if pull > 30:
            affinity += 0.07

    if "Sinker" in usage_pct.index and usage_pct["Sinker"] > 0.25:
        if ld < 18:
            affinity -= 0.05

    return max(0.85, min(1.20, affinity))

def pitcher_affinity_score(primary_pitch: str, batter_profile):
    brl = batter_profile["Brl %"]
    hh = batter_profile["HH %"]
    pull = batter_profile["PullAir %"]
    gb = batter_profile["GB %"]

    score = 1.0

    if primary_pitch == "4-Seam Fastball":
        if brl > 10:
            score += 0.10

    if primary_pitch == "Slider":
        if hh > 40:
            score += 0.08

    if primary_pitch == "Curveball":
        if pull > 30:
            score += 0.06

    if primary_pitch == "Sinker":
        if gb < 40:
            score += 0.05

    return max(0.90, min(1.15, score))
