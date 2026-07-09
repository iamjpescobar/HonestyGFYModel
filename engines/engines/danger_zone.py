import sys
import os

# Ensure project root is in Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import engines.danger_zone as dz
import engines.pitcher_danger_zone as pdz

def build_danger_zone(batter_profile: dict) -> pd.DataFrame:
    """
    Builds a 3x3 danger grid from batter profile:
    High/Mid/Low x Inside/Middle/Outside
    """

    pull = batter_profile["PullAir %"]
    ld = batter_profile["LD %"]
    gb = batter_profile["GB %"]
    brl = batter_profile["Brl %"]
    hh = batter_profile["HH %"]

    danger_score = (
        (pull * 0.25) +
        (ld * 0.35) +
        (brl * 0.20) +
        (hh * 0.20)
    )

    grid = np.array([
        [danger_score * 0.6, danger_score * 0.8, danger_score * 1.0],
        [danger_score * 0.5, danger_score * 0.7, danger_score * 0.9],
        [danger_score * 0.3, danger_score * 0.4, danger_score * 0.6],
    ])

    df = pd.DataFrame(
        grid,
        columns=["Inside", "Middle", "Outside"],
        index=["High", "Mid", "Low"],
    )

    return df
