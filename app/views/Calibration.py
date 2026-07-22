"""
Calibration — the scorecard for this app's own picks.

Shows how the tracked boards have actually performed: picks are
written down by the nightly pipeline BEFORE the games, then graded
against MLB's official box scores after every game is final.

The point is honesty. Any list of good hitters looks sharp on the
nights it lands; the only way to know whether a model is adding value
is to record the picks in advance and count.
"""
import pandas as pd
import streamlit as st

from styles.kc_theme import inject_kc_theme, card, footer, COLOR
from engines.calibration import summary

inject_kc_theme()

st.markdown(
    f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">'
    f'<span style="font-size:20px; font-weight:800; letter-spacing:-0.02em; color:{COLOR["text"]};">CALIBRATION</span>'
    f'</div>',
    unsafe_allow_html=True,
)

data = summary()
tracked = {k: v for k, v in data.items() if v.get("total")}

if not tracked:
    st.info(
        "No graded results yet. The nightly pipeline logs each board's picks before "
        "the games and grades them once every game is final \u2014 the first records "
        "appear after the next completed slate."
    )
    footer()
    st.stop()

for board, s in tracked.items():
    with card(f"cal_{board}"):
        rate = s["rate"]
        col = (COLOR["stat_high"] if rate is not None and rate >= 60
               else COLOR["warn"] if rate is not None and rate >= 45
               else COLOR["error"])
        st.markdown(
            f'<div class="pf-card-title" style="color:{COLOR["gold"]};">{s["label"]}</div>'
            f'<div class="pf-card-subtitle">Share of logged picks that {s["question"]}, '
            f'graded from MLB official box scores.</div>'
            f'<div style="font-size:26px; font-weight:800; color:{col}; margin:6px 0 2px 0;">'
            f'{s["hits"]}/{s["total"]} \u00b7 {rate}%</div>'
            f'<div style="font-size:10.5px; color:{COLOR["text"]}; opacity:0.6;">'
            f'{len(s["days"])} graded slate(s)'
            + (f' \u00b7 {s["dnp"]} pick(s) did not play (excluded, not counted as misses)'
               if s.get("dnp") else "")
            + '</div>',
            unsafe_allow_html=True,
        )

        if s["days"]:
            df = pd.DataFrame([
                {"Date": d["date"],
                 "Hits": str(d["hits"]),
                 "Picks": str(d["total"]),
                 "Rate": f'{d["hits"] / d["total"] * 100:.0f}%' if d["total"] else "\u2014"}
                for d in reversed(s["days"])
            ])
            st.dataframe(df, width="stretch", hide_index=True,
                         height=min(56 + 35 * len(df), 420))

        with st.expander("Per-pick detail"):
            for d in reversed(s["days"]):
                names = []
                for p in d.get("picks", []):
                    mark = {"hit": "\u2705", "miss": "\u274c", "dnp": "\u2014"}.get(
                        p.get("result"), "?")
                    names.append(f'{mark} {p.get("name") or p.get("id")}')
                st.caption(f'**{d["date"]}** \u00b7 ' + " \u00b7 ".join(names))

st.caption(
    "Picks are logged by the nightly data pipeline before first pitch and graded only "
    "after every game on that slate is final \u2014 an in-progress slate is never scored. "
    "Players who did not appear are excluded rather than counted as misses. The pipeline "
    "computes picks slate-wide with a consistent method every night, so the rate measures "
    "the model rather than which pages happened to be open. Note that the tracked HR Edge "
    "picks use the core power ranking (barrel, hard-hit, HR/FB); the Game Card's full Edge "
    "stack adds BvP, zone fit, and bullpen context at request time, so this is a floor on "
    "model quality rather than a ceiling. Records cover a rolling 45-day window."
)

footer()
