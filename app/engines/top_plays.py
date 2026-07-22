"""
Batter ranking scores for the Top Plays panel and the Matchup table.

Built on REAL, LIVE MLB-computed percentile rankings from
baseballsavant.mlb.com (see engines/savant_leaderboard.py), matched by
MLBAM player_id — not name-string matching, not FanGraphs, not this
app's own percentile approximation. This replaced an earlier version
that depended on FanGraphs, which commonly blocks requests from
cloud/dev hosts; Baseball Savant does not have that problem and is
MLB's own first-party data besides.

IMPORTANT — these are still heuristic composite scores (0-100), built
by averaging real percentiles together. They are NOT calibrated
predictive probabilities: nothing here has been backtested against
actual outcomes and graded for accuracy the way a real prediction
model would be. Don't relabel these as "probability" or add a % sign
implying that kind of calibration — every number that FEEDS these
scores is real and live, but the way they're combined is still this
app's own choice, not an official stat.
"""
from engines.savant_leaderboard import get_percentile


# HR/FB scoring anchors — league-average HR/FB sits around 11.5%, so
# that maps to 50 on the same 0-100 scale the Savant percentiles use.
# Weight is deliberately light: HR/FB is the least stable power stat.
_LEAGUE_HRFB = 11.5
_HRFB_WEIGHT = 0.15


def hr_score(player_id, savant_df, hrfb_pct=None):
    """
    Real MLB-computed percentile average of Barrel%, Hard-Hit%, and
    average Exit Velocity —
    both pulled live from Baseball Savant's percentile-rankings
    leaderboard, not derived or approximated by this app.
    Returns None (not 0) when Savant doesn't have this player yet
    (not enough plate appearances, or ID not found) — a 0 would look
    like a real "no power" rating for a real player.
    """
    brl = get_percentile(savant_df, player_id, "brl_percent")
    hh = get_percentile(savant_df, player_id, "hard_hit_percent")
    # Exit velocity percentile added in Phase 2 of the scoring rework —
    # same live Savant source, equal weight with Brl% and HH%. Degrades
    # gracefully: if Savant ever drops the column, the score falls back
    # to the surviving components instead of breaking.
    ev = get_percentile(savant_df, player_id, "exit_velocity")
    parts = [p for p in [brl, hh, ev] if p is not None]
    if not parts:
        return None
    base = sum(parts) / len(parts)

    # HR/FB layer (15%): does his contact quality actually CONVERT to
    # home runs? Barrel/HH/EV measure the process; HR/FB measures the
    # result. It's the noisiest of the power stats, so it's weighted
    # lightly, floored at 25 fly balls (enforced upstream — the metric
    # is None below that), and scaled against the real league anchor
    # (~11.5% HR/FB is roughly league average -> 50 on this scale).
    # Missing HR/FB simply leaves the score at its percentile base
    # rather than penalizing a bat we can't measure.
    hrfb = (hrfb_pct if hrfb_pct is not None else None)
    if hrfb is None:
        return round(base)
    hrfb_scaled = max(0.0, min(100.0, hrfb / _LEAGUE_HRFB * 50.0))
    return round(base * (1 - _HRFB_WEIGHT) + hrfb_scaled * _HRFB_WEIGHT)


def hit_score(player_id, savant_df):
    """
    Real MLB-computed percentile average of xBA (expected batting
    average) and Hard-Hit% — both pulled live from Baseball Savant.
    """
    xba = get_percentile(savant_df, player_id, "xba")
    hh = get_percentile(savant_df, player_id, "hard_hit_percent")
    parts = [p for p in [xba, hh] if p is not None]
    return round(sum(parts) / len(parts)) if parts else None


def k_score(player_id, savant_df):
    """
    Real MLB-computed Whiff% percentile, used directly — no inversion
    needed. Confirmed against real live data before this was built:
    Aaron Judge (elite contact hitter) shows whiff_percent=10.0, i.e. a
    LOW number already means he whiffs less than most of the league.
    That matches this app's "higher K Score = more strikeout-prone"
    convention with no adjustment required.
    """
    return get_percentile(savant_df, player_id, "whiff_percent")


def confidence_tier(sample_size: int) -> tuple:
    """
    Confidence label based purely on sample size — a real, honest
    statistical courtesy (small samples are noisy, full stop), not a
    marketing badge. Returns (label, sample_size) so callers can show
    both, e.g. "Low — n=89".
    Thresholds are this app's own choice, not an industry standard;
    documented here so they're easy to revisit.
    """
    if sample_size >= 300:
        return "High", sample_size
    if sample_size >= 100:
        return "Medium", sample_size
    return "Low", sample_size


def matchup_tier(slam_score: float) -> str:
    """
    Great/Good/Neutral/Weak bucket derived from SLAM. SLAM is now built
    on real xSLG/xwOBA normalized so ~50 = league average (a league-
    average xSLG of .400 and xwOBA of .310 both map to 50) — these
    thresholds are set relative to that real center point, not the old
    0-30ish arbitrary scale. Still a starting point, not a calibrated
    cutoff — revisit once there's real outcome data to check it against.
    """
    if slam_score >= 65:
        return "Great"
    if slam_score >= 55:
        return "Good"
    if slam_score >= 45:
        return "Neutral"
    return "Weak"


def rank_batters(batter_profiles: list, savant_df) -> list:
    """
    batter_profiles: list of {"name": str, "bats": str, "id": str, "profile": dict}
    "id" must be the batter's real MLBAM player ID (already tracked by
    this app's roster engine) — scores are matched on that, not name
    strings, since real IDs don't have the typo/formatting mismatches
    name matching does.

    Returns the same list with hr_score/hit_score/k_score attached.
    HR Score additionally folds in each batter's HR/FB from his
    profile (15% weight, 25-fly-ball floor) when it's available.
    A score is None (never a fabricated 0) when Baseball Savant simply
    doesn't have this player yet — too few plate appearances so far
    this season, most commonly.
    """
    out = []
    for b in batter_profiles:
        pid = b.get("id")
        out.append({
            **b,
            # HR/FB comes from the batter's own windowed profile (the
            # same one the lineup table shows), so the layer respects
            # whatever window the view is on rather than always using
            # season data.
            "hr_score": hr_score(pid, savant_df,
                                 hrfb_pct=(b.get("profile") or {}).get("HR/FB")),
            "hit_score": hit_score(pid, savant_df),
            "k_score": k_score(pid, savant_df),
        })
    return out
