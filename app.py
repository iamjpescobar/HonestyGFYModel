import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# --- SAFETY IMPORT ---
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from pybaseball import batting_stats, pitching_stats

# --- 1. CONFIG & UI ---
st.set_page_config(layout="wide", page_title="Los Cappers Lab", page_icon="🧪")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

st.title("🧪 Los Cappers Lab: Engine Status")

# --- 2. DATA LOADERS ---
@st.cache_data(ttl=3600)
def load_data():
    return batting_stats(2026, qual=10)

# --- 3. TAB ARCHITECTURE ---
tab1, tab2, tab3 = st.tabs(["📊 Analytics", "🎯 Weakspots", "⚡ K-Zone"])

with tab1:
    st.write("Data pipeline active.")
    try:
        df = load_data()
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Data Load Error: {e}")

with tab2:
    if PLOTLY_AVAILABLE:
        st.write("Weakspot Map active.")
    else:
        st.warning("Plotly not installed. Please check requirements.txt")

with tab3:
    st.write("Strikeout Zone active.")
