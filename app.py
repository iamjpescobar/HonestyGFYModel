import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pybaseball import statcast_pitcher, playerid_lookup, batting_stats

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Los Cappers Lab", page_icon="🧪")

# ... [Keep your existing Team ID dictionary and functions here] ...

# --- MAIN APP LOGIC ---
# Ensure all your logic is contained within proper try/except blocks
try:
    games = get_todays_games()
    # Your UI code goes here
except Exception as e:
    st.error(f"App failed to load: {e}")
