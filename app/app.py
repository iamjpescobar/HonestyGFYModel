"""
app.py — Los Cappers entrypoint (unified right sidebar)

This file:
- Renders ONE persistent right-hand sidebar containing: the account card,
  the full page navigation (previously buried in the top-right "Menu"
  dropdown), the Glossary (previously inside the Game Card's own in-page
  sidebar — the only thing carried over from it), a Sign out button, and
  an admin section for admins.
- The Game Card no longer renders its own sidebar; pages get the full
  width of the main column.
- Prevents any leftover code from rendering a second sidebar for
  subscribers by replacing st.sidebar with a pickle-safe shim
  (module-level no-op).
- Ensures admin pages and controls are only included when is_admin()
  returns True.
- Loads page modules by running their file when selected from the sidebar.
"""
import runpy
from pathlib import Path
import os

import streamlit as st

from styles.kc_theme import inject_kc_theme, sport_switcher, COLOR
from auth import require_login, is_admin

st.set_page_config(
    page_title="Los Cappers",
    page_icon="⚾",
    layout="wide"
)

inject_kc_theme()
require_login()  # blocks with a themed login screen until authenticated

# -------------------------
# Admin detection (authoritative server-side is_admin())
# Optional local dev toggle via LC_FORCE_ADMIN env var
# -------------------------
force_admin_env = os.getenv("LC_FORCE_ADMIN", "").lower() in ("1", "true", "yes")
try:
    user_is_admin = is_admin() or force_admin_env
except Exception:
    user_is_admin = bool(force_admin_env)

# -------------------------
# Pickle-safe shim: disable st.sidebar for subscribers
# Use a module-level no-op so Streamlit's caching/pickling won't fail.
# -------------------------
def _lc_no_op(*args, **kwargs):
    return None

class _HiddenSidebar:
    """A minimal shim that swallows common Streamlit sidebar calls.
    Returns a module-level no-op so it is pickle-safe.
    Supports context manager usage: `with st.sidebar: ...`
    """
    def __getattr__(self, name):
        # Return the module-level no-op for any attribute access
        return _lc_no_op

    def __call__(self, *args, **kwargs):
        return _lc_no_op(*args, **kwargs)

    # Support context manager usage: `with st.sidebar: ...`
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

# Replace the sidebar object with the shim for non-admin users
if not user_is_admin:
    st.sidebar = _HiddenSidebar()

# -------------------------
# Sport selection — top-level sport switcher (always visible)
# -------------------------
selected_sport = st.session_state.get("lc_sport", "MLB")

_, _strip_col = st.columns([4, 6])
with _strip_col:
    sport_switcher(active=selected_sport)

# -------------------------
# Helper: build MLB pages list
# Admin pages are only added when include_admin is True.
# -------------------------
def build_mlb_pages(include_admin: bool):
    pages = [
        ("Game Card", "pages/GameCard.py"),
        ("Player of the Day", "pages/Player_Of_The_Day.py"),
        ("Model", "pages/Model.py"),
        ("Pitcher Report", "pages/1_Pitcher_Report.py"),
        ("Pitcher Splits", "pages/1_Pitcher_Splits.py"),
        ("Pitch Mix Splits", "pages/2_Pitch_Mix_Splits.py"),
        ("Lineup Analysis", "pages/2_Lineup_Analysis.py"),
        ("Team Tools", "pages/3_Team_Tools.py"),
        ("KC Lineup Dashboard", "pages/KC_Page.py"),
    ]

    if include_admin:
        pages.append(("Debug Roster (Admin)", "pages/0_Debug_Roster.py"))

    return pages

# -------------------------
# Non-MLB sport page loader
# -------------------------
SPORT_PAGES = {
    "KBO": "pages/KBO.py",
    "WNBA": "pages/WNBA.py",
    "NPB": "pages/NPB.py",
    "NFL": "pages/NFL.py",
    "NBA": "pages/NBA.py",
    "NHL": "pages/NHL.py",
}


def load_page_module(rel_path: str):
    """Executes a sport page file in-place. Pages must NOT call
    st.set_page_config — it's already set once above for the whole app."""
    page_path = Path(__file__).parent / rel_path
    if not page_path.exists():
        st.error(f"Page not found: {rel_path}")
        return
    try:
        runpy.run_path(str(page_path), run_name="__main__")
    except Exception as e:
        st.exception(e)

# -------------------------
# Minimal responsive CSS injection
# -------------------------
def inject_minimal_css():
    css = """
    /* Make images and tables responsive */
    img, table { max-width: 100%; height: auto; }

    /* Right sidebar wrapper */
    .right-sidebar { position: sticky; top: 1rem; padding-left: 0.5rem; padding-right: 0.5rem; }

    /* Admin visual separator (admins only) */
    .admin-sidebar { margin-top: 1rem; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.5rem; }

    /* Defensive: hide any leftover left sidebar or duplicate menu elements that might be injected */
    [data-testid="stSidebar"] { display: none !important; }
    .css-1d391kg { display: none !important; } /* fallback for some Streamlit versions */

    /* Mobile: hide the right column content so main content becomes full width */
    @media (max-width: 900px) {
      .right-sidebar { display: none !important; }
      .admin-sidebar { display: none !important; }
      [data-testid="stAppViewContainer"] .main { width: 100% !important; }
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

inject_minimal_css()


# -------------------------
# Glossary — moved here from the Game Card's old in-page sidebar so it
# lives in the one unified sidebar and is available on every MLB page.
# -------------------------
def render_glossary():
    with st.expander("\U0001F4D6 Glossary"):
        def _section(title):
            st.markdown(
                f'<div style="display:inline-block; padding:3px 10px; border-radius:4px; '
                f'background:{COLOR["error"]}22; border:1px solid {COLOR["error"]}55; '
                f'color:{COLOR["error"]}; font-weight:700; font-size:10.5px; text-transform:uppercase; '
                f'letter-spacing:0.04em; margin:10px 0 6px 0;">{title}</div>',
                unsafe_allow_html=True,
            )

        _section("Colors")
        st.markdown(
            f'<span style="color:{COLOR["player_name"]}; font-weight:700;">Names</span> \u00b7 '
            f'<span style="color:{COLOR["bats_l"]}; font-weight:700;">L</span>/'
            f'<span style="color:{COLOR["bats_r"]}; font-weight:700;">R</span>/'
            f'<span style="color:{COLOR["bats_s"]}; font-weight:700;">S</span> \u00b7 '
            f'<span style="color:{COLOR["error"]}; font-weight:700;">weak</span>\u2192'
            f'<span style="color:{COLOR["warn"]}; font-weight:700;">avg</span>\u2192'
            f'<span style="color:{COLOR["stat_high"]}; font-weight:700;">strong</span>',
            unsafe_allow_html=True,
        )

        _section("Composite Scores")
        st.markdown(
            "- **SLAM** \u2014 real xSLG/xwOBA power score, last 25 PA/BBE/Games. ~50 = league avg.\n"
            "- **HR/Hit/K Score** \u2014 real MLB percentile rankings, matched by player ID.\n"
            "- **Matchup tier** \u2014 bucketed from SLAM. **Confidence** \u2014 sample size only.\n"
            "- **Edge tag** \u2014 from HR/Hit/K Score thresholds, see engines/top_plays.py."
        )
        _section("Contact Quality")
        st.markdown(
            "- **Brl% / HH%** \u2014 Barrel% / Hard-Hit% (95+ mph EV).\n"
            "- **SweetSpot%** \u2014 launch angle 8\u201332\u00b0.\n"
            "- **Blast%** \u2014 (squared-up% \u00d7 100) + bat speed \u2265 164, MLB's real formula."
        )
        _section("Batted Ball Direction")
        st.markdown(
            "- **LD% / FB% / GB%** \u2014 Line Drive / Fly Ball / Ground Ball %.\n"
            "- **PullAir% / PullBrl%** \u2014 pulled fly balls / pulled AND barreled, real "
            "spray-angle math (handedness-aware)."
        )
        _section("Plate Discipline")
        st.markdown(
            "- **SwStr%** \u2014 whiffs / ALL pitches. **Whiff%** \u2014 whiffs / SWINGS only "
            "(different denominator, don't conflate them).\n"
            "- **xSLG / xwOBA** \u2014 MLB's own expected stats from exit velo + launch angle."
        )


# -------------------------
# Render UI
# -------------------------
if selected_sport == "MLB":
    pages = build_mlb_pages(include_admin=user_is_admin)
    menu_titles = [title for title, _ in pages]

    # Resolve the active page BEFORE rendering the main column. The nav
    # radio's widget state (key="lc_nav_radio") is updated by Streamlit
    # at click time, before this rerun executes — reading it here (rather
    # than only after the sidebar renders) means a nav click switches the
    # page on the very next rerun instead of lagging one click behind.
    active_page = st.session_state.get("lc_nav_radio") or st.session_state.get("lc_active_page")
    if active_page not in menu_titles:
        active_page = menu_titles[0] if menu_titles else None

    # Layout: main content + persistent right sidebar
    main_col, right_col = st.columns([8, 2])

    # MAIN: render the currently selected page
    with main_col:
        if active_page:
            module_path = dict(pages).get(active_page)
            if module_path:
                load_page_module(module_path)
            else:
                st.error("Selected page not found.")
        else:
            st.info("No pages available.")

    # RIGHT: the unified sidebar — this replaces both the old "Menu"
    # expander (top right) and the Game Card's old in-page sidebar. The
    # Glossary is the one piece carried over from that old sidebar.
    with right_col:
        st.markdown('<div class="right-sidebar">', unsafe_allow_html=True)

        # Account card — who's signed in and their role
        name = st.session_state.get("name", "")
        role = st.session_state.get("lc_role", "subscriber")
        role_badge_color = COLOR["stat_high"] if role == "admin" else COLOR["warn"]
        st.markdown(
            f'<div class="pf-card" style="padding:12px 14px; margin-bottom:10px;">'
            f'<div style="font-size:13px; font-weight:700; color:{COLOR["text"]};">{name}</div>'
            f'<div style="display:inline-block; margin-top:6px; padding:3px 10px; border-radius:4px; '
            f'background:{role_badge_color}22; color:{role_badge_color}; font-size:10.5px; font-weight:700; '
            f'text-transform:uppercase; letter-spacing:0.05em;">{role}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Page navigation — always visible (was hidden inside the "Menu"
        # dropdown before). Same key as the old radio so nothing else
        # reading lc_nav_radio breaks.
        selected = st.radio(
            "Navigation",
            menu_titles,
            index=menu_titles.index(active_page) if active_page in menu_titles else 0,
            key="lc_nav_radio",
            label_visibility="collapsed",
        )
        st.session_state["lc_active_page"] = selected

        # Glossary — carried over from the Game Card's old sidebar
        render_glossary()

        # Sign out — the native left sidebar (where logout used to live)
        # is hidden/shimmed, so subscribers need it here.
        authenticator = st.session_state.get("lc_authenticator")
        if authenticator is not None:
            authenticator.logout("Sign out", "main", key="lc_sidebar_logout")

        st.markdown("</div>", unsafe_allow_html=True)

        # Admin-only controls: render only for admins and in a separate section
        if user_is_admin:
            st.markdown('<div class="admin-sidebar">', unsafe_allow_html=True)
            st.markdown("### Admin Controls")
            # Admin widgets (only visible to admins)
            # Example:
            # st.checkbox("Show debug logs", key="admin_debug")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.empty()

else:
    # Non-MLB sports load their own page modules
    load_page_module(SPORT_PAGES[selected_sport])