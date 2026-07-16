"""
Los Cappers — entry point (multi-sport header tabs).

This entry file enforces that subscribers never see admin UI. The
subscriber navigation is rendered in a single right-hand sidebar.
Admin pages and controls are only included when is_admin() returns True.
A mobile-friendly expander fallback is provided so the site remains usable
on phones (the right sidebar is visually collapsed on narrow screens).
"""
import runpy
from pathlib import Path
import os

import streamlit as st

from styles.kc_theme import inject_kc_theme, sport_switcher
from auth import require_login, is_admin

st.set_page_config(
    page_title="Los Cappers",
    page_icon="⚾",
    layout="wide"
)

inject_kc_theme()
require_login()  # blocks with a themed login screen until authenticated

# -------------------------
# Sport selection — top-level sport switcher (always visible)
# -------------------------
selected_sport = st.session_state.get("lc_sport", "MLB")

_, _strip_col = st.columns([4, 6])
with _strip_col:
    sport_switcher(active=selected_sport)

# -------------------------
# Helper: build MLB pages dict
# Admin pages are only added when include_admin is True.
# -------------------------
def build_mlb_pages(include_admin: bool):
    pages = {
        "": [
            st.Page("pages/GameCard.py", title="Game Card", icon=":material/stadium:", default=True),
            st.Page("pages/Player_Of_The_Day.py", title="Player of the Day", icon=":material/star:"),
        ],
        "Legacy Tools": [
            st.Page("pages/Model.py", title="Model", icon=":material/monitoring:"),
            st.Page("pages/1_Pitcher_Report.py", title="Pitcher Report", icon=":material/sports_baseball:"),
            st.Page("pages/1_Pitcher_Splits.py", title="Pitcher Splits", icon=":material/split_scene:"),
            st.Page("pages/2_Pitch_Mix_Splits.py", title="Pitch Mix Splits", icon=":material/blender:"),
            st.Page("pages/2_Lineup_Analysis.py", title="Lineup Analysis", icon=":material/groups:"),
            st.Page("pages/3_Team_Tools.py", title="Team Tools", icon=":material/handyman:"),
            st.Page("pages/KC_Page.py", title="KC Lineup Dashboard", icon=":material/dashboard:"),
        ],
    }

    if include_admin:
        pages["Admin"] = [
            st.Page("pages/0_Debug_Roster.py", title="Debug Roster", icon=":material/bug_report:"),
        ]

    return pages

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
# CSS injection (minimal responsive rules)
# If you have a static/styles.css, prefer to edit that file and call load_local_css.
# -------------------------
def inject_minimal_css():
    css = """
    /* Make images and tables responsive */
    img, table { max-width: 100%; height: auto; }

    /* Right sidebar wrapper */
    .right-sidebar { position: sticky; top: 1rem; padding-left: 0.5rem; padding-right: 0.5rem; }

    /* Admin visual separator (admins only) */
    .admin-sidebar { margin-top: 1rem; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.5rem; }

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
# Render navigation or sport page
# -------------------------
if selected_sport == "MLB":
    # Build navigation dict with admin pages only when user_is_admin is True
    navigation = st.navigation(build_mlb_pages(include_admin=user_is_admin), expanded=True)
    # Render the navigation UI (this will create the left-hand navigation in Streamlit's nav)
    navigation.run()

    # Layout: main content + right-hand subscriber sidebar (single visible sidebar)
    main_col, right_col = st.columns([8, 2])

    # MAIN: run the currently selected page's code in the main column
    with main_col:
        # The navigation.run() above will have set the active page and executed it.
        # If you have additional global main-level content to render, place it here.
        # Keep main content behavior unchanged.
        pass

    # RIGHT: subscriber navigation widgets (always) and admin-only controls (only for admins)
    with right_col:
        # Provide an expander so mobile users can access the menu when the column is hidden
        with st.expander("Menu", expanded=False):
            st.markdown('<div class="right-sidebar">', unsafe_allow_html=True)

            # -------------------------
            # Subscriber navigation widgets
            # -------------------------
            # Move your subscriber navigation widgets here. Keep original key= values.
            # Example placeholders (replace with your actual widgets):
            # selected_page = st.radio("Menu", ["Game Card", "Player of the Day", "Model"], key="menu_radio")
            # st.selectbox("Choose team", ["NYM", "PHI"], key="team_select")
            # st.button("Sign out", key="sign_out")
            #
            # IMPORTANT: preserve widget keys to keep session state intact.
            #
            st.markdown("</div>", unsafe_allow_html=True)

        # Admin-only controls: render only for admins
        if user_is_admin:
            st.markdown('<div class="admin-sidebar">', unsafe_allow_html=True)
            st.markdown("### Admin Controls")
            # Insert admin-only widgets here (these will not render for subscribers)
            # Example:
            # st.checkbox("Show debug logs", key="admin_debug")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Defensive: ensure nothing else renders for subscribers
            st.empty()

else:
    # Non-MLB sports load their own page modules (these pages are responsible for their own UI)
    load_page_module(SPORT_PAGES[selected_sport])
