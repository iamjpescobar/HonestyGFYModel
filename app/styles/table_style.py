"""
Reusable red/green heatmap styling for stat tables, matching the
"red = favorable for pitcher, green = favorable for batter" convention.
No extra dependencies (matplotlib etc.) required.
"""
import pandas as pd


def _interpolate_color(t: float):
    """t in [0,1]: 0 = dark navy (bad for batter), 0.5 = neutral, 1 = gold (good for batter)."""
    navy = (17, 34, 64)
    mid = (29, 29, 36)
    gold = (161, 122, 24)
    if t <= 0.5:
        ratio = t / 0.5
        rgb = tuple(int(navy[i] + (mid[i] - navy[i]) * ratio) for i in range(3))
    else:
        ratio = (t - 0.5) / 0.5
        rgb = tuple(int(mid[i] + (gold[i] - mid[i]) * ratio) for i in range(3))
    return rgb


def _color_column(col: pd.Series, invert: bool):
    numeric = pd.to_numeric(col, errors="coerce")
    if numeric.isna().all():
        return [""] * len(col)

    vmin, vmax = numeric.min(), numeric.max()
    if vmin == vmax:
        return ["background-color: #1d1d24; color: #e8e8ec"] * len(col)

    norm = (numeric - vmin) / (vmax - vmin)
    if invert:
        norm = 1 - norm

    styles = []
    for v in norm:
        if pd.isna(v):
            styles.append("")
            continue
        r, g, b = _interpolate_color(float(v))
        styles.append(f"background-color: rgb({r},{g},{b}); color: #f5f5f7")
    return styles


def style_stat_table(df: pd.DataFrame, favor_high=None, favor_low=None):
    """
    Returns a pandas Styler with per-column red/green heatmap coloring.

    favor_high: column names where a HIGHER value is better for the batter (green)
    favor_low:  column names where a LOWER value is better for the batter (green)
    Any column not listed in either is left uncolored.
    """
    favor_high = favor_high or []
    favor_low = favor_low or []

    styler = df.style
    for col in favor_high:
        if col in df.columns:
            styler = styler.apply(lambda c: _color_column(c, invert=False), subset=[col])
    for col in favor_low:
        if col in df.columns:
            styler = styler.apply(lambda c: _color_column(c, invert=True), subset=[col])

    return styler
