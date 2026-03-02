# app.py  —  run with:  streamlit run app.py

import streamlit as st
from pages import setup, dashboard

st.set_page_config(
    page_title="JobBot AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom global CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    body, .stApp { background-color: #030712; color: #f9fafb; }
    .block-container { padding: 2rem 2rem 2rem; max-width: 1100px; }
    .stButton > button {
        border-radius: 10px; font-weight: 600;
        transition: all .2s;
    }
    .stTextInput > div > input,
    .stTextArea > div > textarea {
        background: #1f2937; border: 1px solid #374151;
        color: #f9fafb; border-radius: 8px;
    }
    .stSelectbox > div > div { background: #1f2937; color: #f9fafb; }
    div[data-testid="stMetric"] {
        background: #111827; border: 1px solid #1f2937;
        border-radius: 12px; padding: 16px;
    }
    .status-applied  { color: #4ade80; background: #052e16;
                       border: 1px solid #166534; padding: 2px 10px;
                       border-radius: 9999px; font-size: 12px; }
    .status-pending  { color: #fbbf24; background: #1c1405;
                       border: 1px solid #92400e; padding: 2px 10px;
                       border-radius: 9999px; font-size: 12px; }
    .status-failed   { color: #f87171; background: #1c0505;
                       border: 1px solid #991b1b; padding: 2px 10px;
                       border-radius: 9999px; font-size: 12px; }
    .card {
        background: #111827; border: 1px solid #1f2937;
        border-radius: 14px; padding: 20px; margin-bottom: 12px;
    }
    .log-box {
        background: #000; border-radius: 10px; padding: 16px;
        font-family: monospace; font-size: 12px;
        max-height: 400px; overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# ── Route between setup and dashboard ─────────────────────────────────────
if "profile" not in st.session_state:
    setup.render()
else:
    dashboard.render()
