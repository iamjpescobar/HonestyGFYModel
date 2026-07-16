import json
from pathlib import Path

import streamlit as st

from styles.kc_theme import inject_kc_theme, page_header, card_open, card_close, badge, footer, COLOR
from auth import render_account_sidebar

# NOTE: no st.set_page_config here — app.py already sets it once.

inject_kc_theme()
render_account_sidebar()

_KBO_GAMES = Path(__file__).resolve().parent.parent / "data" / "kbo" / "games.json"
_KBO_PITCHERS = Path(__file__).resolve().parent.parent / "data" / "kbo" / "pitchers.json"

page_header("KBO Analytics", "Korean Baseball Organization — game-level markets", eyebrow="IN ACTIVE DEVELOPMENT")


def _load_games():
    """Reads the KBO slate produced by the nightly pipeline. Returns
    (games, generated_at) or (None, None) when the engine hasn't shipped
    data yet — the page then shows the honest in-development panel
    instead of anything fabricated."""
    try:
        payload = json.loads(_KBO_GAMES.read_text())
        return payload.get("games", []), payload.get("generated_at_kst")
    except Exception:
        return None, None


def _load_pitchers():
    """Reads the real official-KBO pitching leaderboard produced by the
    nightly pipeline. Returns (pitchers, generated_at) or ([], None) when
    it hasn't shipped yet — never fabricated."""
    try:
        payload = json.loads(_KBO_PITCHERS.read_text())
        return payload.get("pitchers", []), payload.get("generated_at_kst")
    except Exception:
        return [], None


def _render_pitching_leaders():
    """Real season pitching lines straight from the official KBO
    leaderboard — shown independent of today's slate so pitcher data is
    always available, even on an off-day or if the slate fetch hiccups."""
    pitchers, p_generated = _load_pitchers()
    if not pitchers:
        return
    st.markdown(card_open("KBO Pitching Leaders", "Real 2026 season lines \u2014 official KBO leaderboard"),
                unsafe_allow_html=True)
    if p_generated:
        st.caption(f"Pitcher data as of {p_generated} KST.")
    dotsp = " \u00b7 "
    for p in pitchers[:15]:
        bits = []
        if p.get("wins") is not None and p.get("losses") is not None:
            bits.append(f'{p["wins"]}-{p["losses"]}')
        if p.get("innings_pitched"):
            bits.append(f'{p["innings_pitched"]} IP')
        if p.get("strikeouts") is not None:
            bits.append(f'{p["strikeouts"]} K')
        if p.get("whip") is not None:
            bits.append(f'{p["whip"]} WHIP')
        for k, lbl in (("saves", "SV"), ("holds", "HLD")):
            v = p.get(k)
            if v and str(v) not in ("0", "-"):
                bits.append(f'{v} {lbl}')
        joined = dotsp.join(bits)
        st.markdown(
            f'<div style="display:flex; justify-content:space-between; gap:12px; '
            f'font-size:12.5px; margin-bottom:6px;">'
            f'<span style="font-weight:700; color:{COLOR["text"]}; white-space:nowrap;">'
            f'{p.get("name", "")} <span style="color:{COLOR["gold"]}; font-weight:400;">'
            f'({p.get("team", "")})</span></span>'
            f'<span style="font-family:\'JetBrains Mono\',monospace; color:{COLOR["gold"]}; '
            f'text-align:right;">ERA {p.get("era", "\u2014")}{dotsp}{joined}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown(card_close(), unsafe_allow_html=True)


games, generated_at = _load_games()

if games is None:
    st.markdown(card_open("\u26be KBO engine is being connected"), unsafe_allow_html=True)
    st.markdown(
        f'<div style="color:{COLOR["gold"]}; font-size:14px; line-height:1.7;">'
        f'KBO coverage is in active development on the same standard as the MLB engine: '
        f'every number traced to a real, verifiable source \u2014 no placeholders, no estimates. '
        f'This page lights up with the real slate the moment the data pipeline ships; '
        f'nothing appears here before that.'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(card_close(), unsafe_allow_html=True)

    st.markdown(card_open("What launches first"), unsafe_allow_html=True)
    for name, desc in [
        ("Daily Slate", "Every NPB game with starters, park, and start time (JST + ET) - start times shown in KST and ET"),
        ("Team Profiles", "Real offense/pitching form for totals and run-line handicapping"),
        ("Starter Form", "Season and recent-start lines for the day\'s probables"),
    ]:
        st.markdown(
            f'<div style="margin-bottom:12px;">'
            f'<div style="font-weight:700; color:{COLOR["text"]}; font-size:13.5px;">{name}</div>'
            f'<div style="color:{COLOR["gold"]}; font-size:12.5px;">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown(card_close(), unsafe_allow_html=True)
    st.markdown(badge("MLB \u2014 live now", "good") + badge("KBO \u2014 in development", "accent"), unsafe_allow_html=True)
    _render_pitching_leaders()
    footer()
    st.stop()

# ------------------------------------------------------------
# REAL SLATE (renders only when the pipeline has shipped data)
# ------------------------------------------------------------
if generated_at:
    st.caption(f"Slate data as of {generated_at} KST \u2014 refreshed by the nightly pipeline.")

_render_pitching_leaders()

if not games:
    st.info("No KBO games on today\'s schedule \u2014 likely a league off-day.")
else:
    def _team_line(g, side):
        """One team's real season line — only renders fields the data
        actually contains."""
        name = g.get(side, "TBD")
        bits = []
        if g.get(f"{side}_record"):
            bits.append(f'{g[f"{side}_record"]}')
        if g.get(f"{side}_rs_pg") is not None and g.get(f"{side}_ra_pg") is not None:
            bits.append(f'{g[f"{side}_rs_pg"]} RS / {g[f"{side}_ra_pg"]} RA per game')
        if g.get(f"{side}_last10"):
            bits.append(f'L10: {g[f"{side}_last10"]}')
        if not bits:
            return ""
        dot = " \u00b7 "
        joined = dot.join(bits)
        return (f'<div style="display:flex; justify-content:space-between; gap:12px; '
                f'font-size:12.5px; margin-bottom:6px;">'
                f'<span style="font-weight:700; color:{COLOR["text"]};">{name}</span>'
                f'<span style="font-family:\'JetBrains Mono\',monospace; color:{COLOR["gold"]};">'
                f'{joined}</span></div>')

    for g in games:
        status = g.get("status", "scheduled")
        subtitle = f'{g.get("stadium", "")} \u00b7 {g.get("time_kst", "TBD")} KST / {g.get("time_et", "TBD")} ET'
        st.markdown(card_open(f'{g.get("away", "TBD")} @ {g.get("home", "TBD")}', subtitle), unsafe_allow_html=True)

        status_style = {"postponed": "bad", "final": "good", "final (tie)": "good"}.get(status, "neutral")
        badges = badge(status.upper(), status_style)
        if g.get("final"):
            badges += badge(g["final"], "accent")
        if g.get("starters_raw"):
            badges += badge(f'Announced starters: {g["starters_raw"]}', "neutral")
        else:
            badges += (badge(f'Away SP: {g.get("away_starter", "TBD")}', "neutral")
                       + badge(f'Home SP: {g.get("home_starter", "TBD")}', "neutral"))
        st.markdown(badges, unsafe_allow_html=True)

        stats_html = _team_line(g, "away") + _team_line(g, "home")
        if g.get("h2h"):
            stats_html += (f'<div style="font-size:11.5px; color:{COLOR["gold"]}; '
                           f'margin-top:4px;">Season H2H: {g["h2h"]}</div>')
            det = g.get("h2h_detail") or {}
            if det.get("avg_total") is not None:
                stats_html += (
                    f'<div style="font-size:11px; color:{COLOR["text"]}; margin-top:2px;">'
                    f'H2H runs: {g.get("away")} {det.get("away_avg_runs")} R/G vs '
                    f'{g.get("home")} {det.get("home_avg_runs")} R/G \u00b7 '
                    f'Avg total in series: <b>{det.get("avg_total")}</b></div>')
            if det.get("scorelines"):
                joined = " \u00b7 ".join(det["scorelines"][:6])
                stats_html += (f'<div style="font-size:10.5px; color:{COLOR["gold"]}; '
                               f'opacity:0.85; margin-top:2px;">{joined}</div>')
        if stats_html:
            st.markdown(f'<div style="margin-top:10px;">{stats_html}</div>', unsafe_allow_html=True)
        st.markdown(card_close(), unsafe_allow_html=True)

footer()