"""
Strikeout Board — projected K line for every posted probable starter
on today's MLB slate, sorted highest projection first.

Runs inside app.py's loader (no st.set_page_config here). The formula
and all inputs are shown on the page — see engines/k_projection.py.
"""
import pandas as pd
import streamlit as st

from styles.kc_theme import inject_kc_theme, card, footer, COLOR
from styles.table_style import style_stat_table
from engines.k_projection import get_slate_k_projections

inject_kc_theme()

st.markdown(
    f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">'
    f'<span style="font-size:20px; font-weight:800; letter-spacing:-0.02em; color:{COLOR["text"]};">STRIKEOUT</span>'
    f'<span style="font-size:20px; font-weight:800; letter-spacing:-0.02em; color:{COLOR["stat_high"]};">BOARD</span>'
    f'</div>',
    unsafe_allow_html=True,
)

rows, warning = get_slate_k_projections()

if warning:
    st.warning(warning)

projected = [r for r in rows if r.get("proj") is not None]
unprojected = [r for r in rows if r.get("proj") is None]

if not rows:
    st.info("No games on today's slate.")
else:
    with card("k_board"):
        st.markdown(
            f'<div class="pf-card-title" style="color:{COLOR["gold"]};">Projected K \u2014 today\'s probable starters</div>'
            f'<div class="pf-card-subtitle">proj K = (K/9 \u00f7 9) \u00d7 innings per start \u00d7 opponent K factor \u2014 '
            f'every input is in the table. This app\'s own projection from real Statcast + MLB team stats, '
            f'not a sportsbook line and not a certified prediction.</div>',
            unsafe_allow_html=True,
        )
        if projected:
            df = pd.DataFrame([
                {
                    "Pitcher": r["pitcher"],
                    "Game": r["matchup"],
                    "Team": r["team"],
                    "Opp": r["opp"],
                    "IP/GS": r["ip_gs"],
                    "K/9": r["k9"],
                    "Opp K%": r["opp_k_pct"],
                    "Proj K": r["proj"],
                }
                for r in projected
            ]).sort_values("Proj K", ascending=False).set_index("Pitcher")
            st.dataframe(
                style_stat_table(
                    df,
                    favor_high=["Proj K", "K/9", "Opp K%"],
                    gradient=True,
                ),
                width="stretch",
                height=min(56 + 35 * len(df), 900),
            )
            st.caption(
                "IP/GS is estimated from Statcast out events (same basis as the Splits table \u2014 "
                "no official box-score innings feed). Opp K% is that lineup's real season strikeout "
                "rate from MLB's team stats; its effect is capped at \u00b115%. Compare Proj K against "
                "your book's line \u2014 the gap is the read, not the raw number."
            )
        else:
            st.info("No projectable starters yet \u2014 probables usually fill in through the morning.")

    if unprojected:
        with st.expander(f"\u26a0\ufe0f Not projected ({len(unprojected)})"):
            for r in unprojected:
                st.caption(f"{r['matchup']} \u2014 {r['pitcher']} ({r['team']}): {r.get('status', 'no data')}")

footer()