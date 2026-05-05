import os
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from openai import OpenAI
from chart_module import render_chart_module
import plotly.graph_objects as go
import time

if "last_call" not in st.session_state:
    st.session_state.last_call = 0

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="AInvest",
    layout="wide",
)

# -----------------------------
# API key / OpenAI client
# -----------------------------
api_key = None

try:
    api_key = st.secrets.get("OPENAI_API_KEY", None)
except Exception:
    api_key = None

if not api_key:
    api_key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=api_key) if api_key else None

# -----------------------------
# Session state
# -----------------------------
if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "F"

if "chart_timeframe" not in st.session_state:
    st.session_state.chart_timeframe = "Today"

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
<style>
:root {
    --bg: #050B1A;
    --panel: #091733;
    --panel-2: #0B1633;
    --panel-soft: #112042;
    --border: rgba(255,255,255,0.10);
    --grid: rgba(255,255,255,0.06);
    --text: #E7EEF9;
    --muted: rgba(231,238,249,0.72);
    --blue: #3A8DFF;
    --blue-2: #4B5DFF;
    --green: #2EE59D;
    --red: #FF4D6D;
    --amber: #FFB020;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background:
        radial-gradient(1000px 700px at 15% 10%, rgba(58,141,255,0.10), transparent 55%),
        radial-gradient(800px 600px at 85% 18%, rgba(46,229,157,0.06), transparent 55%),
        var(--bg);
    color: var(--text);
}

.main, [data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    max-width: 1520px;
    padding-top: 1.1rem;
    padding-bottom: 1.25rem;
}

div[data-testid="stVerticalBlock"] > div:has(.top-brand) {
    margin-bottom: 1rem;
}

.top-brand {
    display: flex;
    align-items: center;
    gap: 14px;
    color: var(--text);
    min-height: 52px;
}

.logo-box {
    font-size: 2rem;
    line-height: 1;
}

.brand-title {
    font-size: 2.1rem;
    font-weight: 800;
    line-height: 1.0;
    letter-spacing: -0.03em;
    color: var(--text);
}

.brand-subtitle {
    margin-top: 0.15rem;
    font-size: 1rem;
    color: var(--muted);
}

.panel-card {
    background: linear-gradient(180deg, rgba(9,23,51,0.96), rgba(5,11,26,0.97));
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1.35rem 1.35rem 1.2rem 1.35rem;
    box-shadow: 0 18px 40px rgba(0,0,0,0.28);
    color: var(--text);
}

.right-card {
    min-height: 0;
}

.summary-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
}

.summary-name {
    font-size: 2.25rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text);
}

.signal-pill {
    display: inline-block;
    padding: 0.48rem 0.95rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.94rem;
    letter-spacing: 0.01em;
    color: var(--text);
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.05);
}

.metrics-2x2 {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 0.6rem;
    margin-bottom: 1rem;
}

.metric-tile {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1rem 1rem 0.95rem 1rem;
    min-height: 96px;
}

.metric-label {
    color: var(--muted);
    font-size: 0.95rem;
    margin-bottom: 0.45rem;
}

.metric-value {
    color: var(--text);
    font-size: 1.12rem;
    font-weight: 800;
}

.signal-summary {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1rem 1rem 1rem 1rem;
    margin-top: 0.4rem;
}

.signal-summary-title {
    font-size: 1.05rem;
    font-weight: 800;
    margin-bottom: 0.85rem;
    color: var(--text);
}

.signal-summary p {
    margin: 0.15rem 0 0.55rem 0;
    color: var(--text);
    line-height: 1.55;
    font-size: 0.98rem;
}

.source-note {
    color: var(--muted);
    font-size: 0.93rem;
    margin-top: 1rem;
}

.bottom-card {
    background: linear-gradient(180deg, rgba(9,23,51,0.96), rgba(5,11,26,0.97));
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1.25rem 1.25rem 1.1rem 1.25rem;
    box-shadow: 0 18px 40px rgba(0,0,0,0.22);
}

.card-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 0.85rem;
}

.card-heading-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.icon-chip {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: #4B5DFF;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1rem;
    font-weight: 700;
    flex: 0 0 auto;
}

.card-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--text);
}

.insight-body {
    color: var(--text);
    line-height: 1.7;
    font-size: 1rem;
}

.insight-body ul {
    margin-top: 0.7rem;
    padding-left: 1.2rem;
}

.headline-list {
    margin-top: 0.2rem;
}

.headline-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 0.75rem;
    padding: 0.95rem 0;
    border-top: 1px solid rgba(255,255,255,0.08);
    align-items: center;
}

.headline-row:first-child {
    border-top: 1px solid rgba(255,255,255,0.08);
}

.headline-title {
    color: var(--text);
    font-size: 1rem;
}

.headline-meta {
    color: var(--muted);
    font-size: 0.95rem;
    white-space: nowrap;
}

.view-all {
    color: #39A8FF;
    font-weight: 700;
    font-size: 1rem;
}

.footer-note {
    text-align: center;
    color: var(--muted);
    font-size: 0.95rem;
    margin-top: 1.2rem;
    padding-bottom: 0.5rem;
}

div[data-testid="stTextInput"] label,
div[data-testid="stRadio"] label {
    color: var(--muted) !important;
}

div[data-testid="stTextInput"] input {
    background: rgba(9,23,51,0.96) !important;
    color: var(--text) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 16px !important;
    min-height: 54px !important;
    padding-left: 1rem !important;
    font-size: 1rem !important;
    box-shadow: none !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: rgba(231,238,249,0.45) !important;
}

div[data-testid="stButton"] > button {
    width: 100%;
    min-height: 54px;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.08) !important;
    background: linear-gradient(135deg, #4B5DFF 0%, #3A8DFF 100%) !important;
    color: white !important;
    font-weight: 700;
    font-size: 1rem;
    box-shadow: none !important;
}

div[data-testid="stButton"] > button:hover {
    filter: brightness(1.05);
    border-color: rgba(255,255,255,0.14) !important;
}

div[data-testid="stRadio"] > div {
    margin-top: -0.2rem;
}

div[data-baseweb="radio"] > div {
    gap: 0.55rem;
}

div[data-baseweb="radio"] label {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 0.42rem 0.95rem;
    border-radius: 12px;
    color: #f8fafc !important;
    font-weight: 700;
    transition: all 0.18s ease;
    opacity: 1 !important;
}

div[data-baseweb="radio"] label span {
    color: #f8fafc !important;
    opacity: 1 !important;
}

div[data-baseweb="radio"] label:has(input:checked) {
    background: linear-gradient(135deg, #4B5DFF 0%, #3A8DFF 100%);
    border-color: rgba(255,255,255,0.14);
    color: white;
}

div[data-baseweb="radio"] label span {
    color: inherit !important;
}

hr {
    border-color: rgba(255,255,255,0.10);
}

[data-testid="stMarkdownContainer"] h3 {
    color: var(--text);
}

@media (max-width: 1200px) {
    .metrics-2x2 {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 900px) {
    .brand-title {
        font-size: 1.7rem;
    }
    .summary-name {
        font-size: 1.8rem;
    }
}

div[data-testid="stRadio"] label,
div[data-testid="stRadio"] span {
    color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 700 !important;
}

div[data-testid="stRadio"] div {
    color: #ffffff !important;
    opacity: 1 !important;
}
.welcome-hero {
    background: linear-gradient(180deg, rgba(9,23,51,0.96), rgba(5,11,26,0.97));
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 2.2rem 2.2rem 2rem 2.2rem;
    box-shadow: 0 18px 40px rgba(0,0,0,0.22);
    overflow: hidden;
    position: relative;
    min-height: 420px;
}

.welcome-grid {
    display: grid;
    grid-template-columns: 1.15fr 0.95fr;
    gap: 1.5rem;
    align-items: center;
}

.welcome-pill {
    display: inline-block;
    padding: 0.45rem 0.85rem;
    border-radius: 12px;
    border: 1px solid rgba(58,141,255,0.45);
    color: #6fe3ff;
    font-weight: 700;
    font-size: 0.92rem;
    letter-spacing: 0.01em;
    margin-bottom: 1.2rem;
    background: rgba(58,141,255,0.08);
}

.welcome-title {
    font-size: 4rem;
    font-weight: 900;
    line-height: 1.02;
    letter-spacing: -0.05em;
    color: var(--text);
    margin-bottom: 1rem;
}

.welcome-title .accent {
    color: #6fe3ff;
}

.welcome-subtitle {
    font-size: 1.15rem;
    line-height: 1.65;
    color: rgba(231,238,249,0.9);
    max-width: 720px;
    margin-bottom: 1.6rem;
}

.welcome-features {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.welcome-feature {
    display: flex;
    align-items: flex-start;
    gap: 0.9rem;
}

.welcome-feature-icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(75,93,255,0.10);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6fe3ff;
    font-size: 1.3rem;
    flex: 0 0 auto;
}

.welcome-feature-title {
    color: var(--text);
    font-size: 1.15rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}

.welcome-feature-text {
    color: var(--muted);
    font-size: 1rem;
    line-height: 1.5;
}

.welcome-art {
    position: relative;
    min-height: 320px;
    border-radius: 20px;
    overflow: hidden;
    background:
        radial-gradient(500px 260px at 70% 10%, rgba(58,141,255,0.18), transparent 60%),
        linear-gradient(180deg, rgba(5,11,26,0.2), rgba(5,11,26,0.0));
}

.welcome-bars {
    position: absolute;
    right: 1.5rem;
    bottom: 0.5rem;
    left: 1.5rem;
    display: flex;
    align-items: flex-end;
    gap: 0.55rem;
    height: 48%;
    opacity: 0.45;
}

.welcome-bar {
    flex: 1 1 auto;
    border-radius: 10px 10px 0 0;
    background: linear-gradient(180deg, rgba(58,141,255,0.30), rgba(58,141,255,0.08));
}

.welcome-line {
    position: absolute;
    inset: 0;
}

.welcome-line svg {
    width: 100%;
    height: 100%;
}

.ticker-section {
    background: linear-gradient(180deg, rgba(9,23,51,0.96), rgba(5,11,26,0.97));
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 1.5rem;
    box-shadow: 0 18px 40px rgba(0,0,0,0.22);
}

.ticker-section-title {
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.15rem;
}

.ticker-section-subtitle {
    color: var(--muted);
    font-size: 1rem;
    margin-bottom: 1.3rem;
}

.ticker-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 1.25rem;
}

.ticker-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1.15rem 1.1rem;
    min-height: 150px;
}

.ticker-symbol {
    color: var(--text);
    font-size: 1.9rem;
    font-weight: 900;
    margin-bottom: 0.2rem;
}

.ticker-name {
    color: var(--muted);
    font-size: 1rem;
    margin-bottom: 1rem;
}

.ticker-price {
    color: var(--text);
    font-size: 1.05rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
}

.ticker-change-pos {
    color: #2EE59D;
    font-size: 1rem;
    font-weight: 800;
}

.ticker-change-neg {
    color: #FF4D6D;
    font-size: 1rem;
    font-weight: 800;
}

.welcome-tip {
    margin-top: 1.4rem;
    background: linear-gradient(180deg, rgba(9,23,51,0.96), rgba(5,11,26,0.97));
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.15rem 1.3rem;
    display: flex;
    align-items: center;
    gap: 0.9rem;
    color: var(--text);
}

.welcome-tip-icon {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    background: linear-gradient(135deg, #4B5DFF 0%, #3A8DFF 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    flex: 0 0 auto;
}

@media (max-width: 1200px) {
    .welcome-grid {
        grid-template-columns: 1fr;
    }

    .ticker-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .welcome-features {
        grid-template-columns: 1fr;
    }
}


/* Segmented Control (Mode Toggle) */
div[data-baseweb="button-group"] {
    display: flex !important;
    gap: 12px !important;
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.10);
    padding-bottom: 6px;
}

div[data-baseweb="button-group"] button {
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.65) !important;
    font-weight: 600 !important;
    padding: 6px 4px !important;
    pointer-events: auto !important;
    cursor: pointer !important;
}
div[data-baseweb="button-group"] {
    pointer-events: auto !important;
}
/* selected tab */
div[data-baseweb="button-group"] button[aria-pressed="true"] {
    color: #FFFFFF !important;
    border-bottom: 2px solid #FFB020 !important;
}

/* underline selected radio (safe version) */
div[role="radiogroup"] label {
    border-bottom: 2px solid transparent;
    padding-bottom: 4px;
}

div[role="radiogroup"] label:has(input:checked) {
    border-bottom: 2px solid #FFB020;
}
/* hide radio circle ONLY */
div[role="radiogroup"] label > div:first-child {
    display: none !important;
}

/* Portfolio Lab cards */
.portfolio-card {
    background: rgba(10, 18, 40, 0.88);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 18px 18px 16px 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.22);
}

.portfolio-card h3 {
    margin: 0 0 8px 0;
    color: #F5F7FB;
    font-size: 1.05rem;
    font-weight: 700;
}

.portfolio-subtext {
    color: rgba(231,238,249,0.68);
    font-size: 0.88rem;
    margin-bottom: 12px;
}

.portfolio-placeholder {
    background: rgba(20, 36, 78, 0.65);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    min-height: 70px;
    padding: 14px;
    color: rgba(231,238,249,0.5);
    font-size: 0.9rem;
}

.portfolio-placeholder.tall {
    min-height: 220px;
}

.portfolio-placeholder.medium {
    min-height: 150px;
}

/* Portfolio buttons (default state) */
div[data-testid="stButton"] button {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    color: #E7EEF9 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    transition: all 0.2s ease;
}

/* Hover = subtle blue hint */
div[data-testid="stButton"] button:hover {
    background: rgba(58, 189, 255, 0.10) !important;
    border-color: rgba(58, 189, 255, 0.35) !important;
    color: #FFFFFF !important;
}

/* ACTIVE / SELECTED (this is the magic) */
div[data-testid="stButton"] button[kind="primary"] {
    background: rgba(58, 189, 255, 0.14) !important;
    border: 1px solid rgba(58, 189, 255, 0.75) !important;
    color: #73CFFF !important;
    box-shadow: 0 0 14px rgba(58, 189, 255, 0.22) !important;
}

/* Dark input (base) */
div[data-testid="stTextInput"] input {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    color: #E7EEF9 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    transition: all 0.2s ease;
}

/* Focus = subtle glow (like your reference UI) */
div[data-testid="stTextInput"] input:focus {
    outline: none !important;
    border: 1px solid rgba(58, 189, 255, 0.55) !important;
    box-shadow: 0 0 10px rgba(58, 189, 255, 0.18) !important;
}

/* Placeholder styling */
div[data-testid="stTextInput"] input::placeholder {
    color: rgba(231,238,249,0.45) !important;
}

/* Kill ALL white input backgrounds */
div[data-testid="stTextInput"] {
    background: transparent !important;
}

div[data-testid="stTextInput"] > div {
    background: transparent !important;
}

/* Force dark styling on the actual input */
div[data-testid="stTextInput"] input {
    background-color: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    color: #E7EEF9 !important;
}
/* Fix white Streamlit input box (FINAL fix) */
div[data-testid="stTextInput"] > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 8px !important;
}

div[data-testid="stTextInput"] input {
    background: transparent !important;
    color: #E7EEF9 !important;
}

div[data-testid="stTextInput"] input:focus {
    background: transparent !important;
    border: none !important;
    box-shadow: 0 0 8px rgba(58,189,255,0.18) !important;
}
/* Remove white border from Add Ticker input */
div[data-testid="stTextInput"] div[data-baseweb="input"] {
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
    outline: none !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
    border: 1px solid rgba(58,189,255,0.35) !important;
    box-shadow: 0 0 8px rgba(58,189,255,0.12) !important;
    outline: none !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"] input {
    background: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

/* -----------------------------
   Compact Portfolio Controls
------------------------------*/

/* Reduce vertical spacing inside left panel */
.portfolio-card,
div[data-testid="stVerticalBlock"]:has(button[key="portfolio_analyze"]) {
    gap: 6px !important;
}

/* Ticker chips */
button[key^="remove_"] {
    height: 18px !important;
    min-height: 18px !important;
    font-size: 0.65rem !important;
    padding: 0px 2px !important;
    line-height: 1 !important;
    border-radius: 5px !important;
    box-shadow: none !important;
}

/* Add ticker input */
div[data-testid="stTextInput"] input {
    min-height: 36px !important;
    font-size: 0.9rem !important;
}

/* + Add button */
button[key="portfolio_add_ticker"] {
    height: 15px !important;          /* 🔥 controls actual height */
    min-height: 15px !important;

    font-size: 0.65rem !important;    /* text size */

    padding: 0px 2px !important;      /* 🔥 biggest size driver */
    line-height: 1 !important;

    border-radius: 4px !important;
    box-shadow: none !important;
}

/* Weight buttons */
button[key="portfolio_equal_weight"],
button[key="portfolio_custom_weights"] {
    height: 18px !important;
    min-height: 18px !important;
    font-size: 0.65rem !important;
    padding: 0px 2px !important;
    line-height: 1 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}

/* Analyze button */
button[key="portfolio_analyze"] {
    height: 18px !important;
    min-height: 18px !important;
    font-size: 0.65rem !important;
    padding: 0px 2px !important;
    line-height: 1 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}

/* Section titles smaller */
h3 {
    font-size: 1.05rem !important;
}

/* Reduce spacing under "Build Your Portfolio" */
.stMarkdown + div {
    margin-top: 6px !important;
}

/* Reduce chip grid spacing */
div[data-testid="stHorizontalBlock"] {
    gap: 6px !important;
}

/* Compact ALL Portfolio Lab buttons */
div[data-testid="stButton"] button {
    min-height: 22px !important;
    height: 22px !important;
    padding: 0px 8px !important;
    font-size: 0.72rem !important;
    line-height: 1 !important;
}

/
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Data loading
# -----------------------------
@st.cache_data
def load_top_signals() -> pd.DataFrame:
    df = pd.read_csv("data/top_signals.csv")
    df["Ticker"] = df["Ticker"].astype(str).str.upper()
    df["Up Probability"] = pd.to_numeric(df["Up Probability"], errors="coerce")
    df = df.dropna(subset=["Up Probability"])
    return df.sort_values("Up Probability", ascending=False).reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=900)
def fetch_recent_headlines(ticker: str) -> list[str]:
    titles = []
    try:
        stock = yf.Ticker(ticker)

        raw_news = []
        try:
            raw_news = stock.get_news()
        except Exception:
            pass

        if not raw_news:
            try:
                raw_news = stock.news
            except Exception:
                raw_news = []

        for item in raw_news[:6]:
            title = None
            if isinstance(item, dict):
                title = (
                    item.get("title")
                    or item.get("content", {}).get("title")
                    or item.get("headline")
                )

            if title and isinstance(title, str):
                clean = title.strip()
                if clean and clean not in titles:
                    titles.append(clean)

            if len(titles) >= 3:
                break
    except Exception:
        return []

    return titles[:3]


# -----------------------------
# Helpers
# -----------------------------
def get_model_risk(confidence: float) -> str:
    if confidence >= 75:
        return "Medium"
    if confidence >= 60:
        return "Medium"
    if confidence >= 50:
        return "Medium-High"
    return "High"


def get_fallback_risk(confidence: float) -> str:
    if confidence >= 55:
        return "Medium"
    if confidence <= 45:
        return "High"
    return "Medium"


def get_signal(confidence: float) -> tuple[str, str]:
    if confidence >= 70:
        return "Bullish Bias", "#334155"
    elif confidence >= 50:
        return "Neutral / Mixed", "#334155"
    else:
        return "Bearish Bias", "#334155"


def compact_ai_summary(
    latest_price: float | None,
    daily_change_pct: float | None,
    vwap: float | None,
    high_level: float | None,
    low_level: float | None,
) -> str:
    line_1 = "Mixed technicals with short-term weakness."
    if daily_change_pct is not None:
        if daily_change_pct >= 1:
            line_1 = "Short-term momentum is constructive with price pressing higher."
        elif daily_change_pct <= -1:
            line_1 = "Short-term weakness is building with downside pressure visible."

    line_2 = "Price is trading near near-term levels."
    if latest_price is not None and vwap is not None:
        if latest_price >= vwap:
            line_2 = "Price is holding above VWAP with intraday support."
        else:
            line_2 = "Price is trading below VWAP with softer momentum."

    line_3 = "Watch nearby support and resistance."
    if low_level is not None and high_level is not None:
        line_3 = f"Watch ${low_level:.0f} support and ${high_level:.0f} resistance."

    return f"{line_1}\n{line_2}\n{line_3}"

def get_welcome_tickers() -> list[dict[str, str]]:
    return [
        {"symbol": "AAPL", "name": "Apple Inc.", "price": "$175.43", "change": "+1.28%", "cls": "ticker-change-pos"},
        {"symbol": "NVDA", "name": "NVIDIA Corp.", "price": "$932.17", "change": "+2.14%", "cls": "ticker-change-pos"},
        {"symbol": "TSLA", "name": "Tesla, Inc.", "price": "$168.22", "change": "-0.73%", "cls": "ticker-change-neg"},
        {"symbol": "MSFT", "name": "Microsoft Corp.", "price": "$420.15", "change": "+0.91%", "cls": "ticker-change-pos"},
        {"symbol": "BTC-USD", "name": "Bitcoin", "price": "$64,812.45", "change": "+1.87%", "cls": "ticker-change-pos"},
    ]

def get_stress_bg(color):
    if color == "#FF4D6D":
        return "rgba(255,77,109,0.08)"
    if color == "#2EE59D":
        return "rgba(46,229,157,0.08)"
    if color == "#FFB020":
        return "rgba(255,176,32,0.08)"
    return "rgba(255,255,255,0.03)"

# -----------------------------
#  Stock Lens AI — Trader Desk Voic
# -----------------------------
@st.cache_data(show_spinner=False, ttl=300)
def generate_ai_explanation(
    ticker: str,
    confidence: float,
    risk: str,
    source_used: str,
    latest_price: float | None,
    daily_change_pct: float | None,
    headlines: tuple[str, ...],
    extra_inputs: tuple[str, ...] | None = None,
) -> str:
    if not api_key or client is None:
        return "AI trader insight unavailable because OPENAI_API_KEY is not set."

    price_text = f"${latest_price:.2f}" if latest_price is not None else "N/A"
    change_text = f"{daily_change_pct:+.2f}%" if daily_change_pct is not None else "N/A"

    if headlines:
        headline_block = "\n".join([f"- {h}" for h in headlines])
    else:
        headline_block = "No recent headlines available."

    if extra_inputs:
        extra_input_block = "\n".join([f"- {item}" for item in extra_inputs])
    else:
        extra_input_block = "No structured signals available."

    prompt = f"""
You are writing a trader-facing desk note for a dark fintech dashboard.

Write a concise institutional note.

Rules:
- 4 short paragraphs max
- direct, trader-facing language
- no hype
- no storytelling
- mention support / resistance tone if helpful
- keep it sharp and readable in a UI card

Inputs:
Ticker: {ticker}
Confidence: {confidence:.2f}%
Risk: {risk}
Source used: {source_used}
Latest price: {price_text}
Daily change: {change_text}

Structured signals:
{extra_input_block}

Recent headlines:
{headline_block}
"""



    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        text = (response.output_text or "").strip()
        return text if text else "AI trader insight unavailable right now."
    except Exception:
        return "AI trader insight unavailable right now."
    
# -----------------------------
# Portfolio Lab AI — Portfolio Manager Voice
# -----------------------------


@st.cache_data(show_spinner=False, ttl=300)
def generate_portfolio_brief(tickers, metrics, timeframe):
    if not api_key or client is None:
        return "AI portfolio brief unavailable because OPENAI_API_KEY is not set."

    if not metrics:
        return "Portfolio brief unavailable until portfolio metrics load."

    holdings_text = ", ".join([f"{t}: {w:.1f}%" for t, w in metrics["weights"].items()])

    prompt = f"""
   
    You are a portfolio manager reviewing a portfolio on your desk.

    Write like internal PM notes — concise, sharp, slightly informal.

    Focus on:
    - what this portfolio actually is
    - what is driving returns
    - where risk is concentrated
    - what would break the setup
    - what matters next

    Portfolio:
    Tickers: {", ".join(tickers)}
    Holdings: {holdings_text}
    Timeframe: {timeframe}

    Rules:
    - 1 tight paragraph (no fluff)
    - then 2–3 short bullets
    - bullets should be punchy (not full sentences if possible)
    - do NOT restate metrics already shown above
    - avoid phrases like "this suggests", "this indicates"
    - no generic advice
    - no textbook language
    - no hype

    Tone:
    - internal
    - efficient
    - slightly blunt
    - write in fragments when possible (not full sentences)
    - avoid full sentences — prefer fragmented desk-style thoughts

    Add ONE final line:

    - a blunt takeaway (max 12 words)

    - think: "Concentrated tech risk. SPY won’t save you."
    """

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        return (response.output_text or "").strip()
    except Exception:
        return "AI portfolio brief unavailable right now."
    
@st.cache_data(show_spinner=False, ttl=900)
def build_portfolio_benchmark_chart(tickers, timeframe):
    period_map = {
        "1Y": "1y",
        "3Y": "3y",
        "5Y": "5y",
        "10Y": "10y",
    }

    period = period_map.get(timeframe, "5y")

    benchmark_sets = {
        "SPY": ["SPY"],
        "Growth Strategy": ["QQQ", "SMH"],
        "Concentrated Alpha": ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"],
        "Defensive Allocation": ["SPY", "TLT"],
    }

    all_tickers = list(set(tickers + ["SPY", "QQQ", "SMH", "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "TLT"]))

    prices = yf.download(
        all_tickers,
        period=period,
        auto_adjust=True,
        progress=False
    )["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    prices = prices.dropna(axis=1, how="all").ffill().dropna()

    returns = prices.pct_change().dropna()

    portfolio_returns = returns[tickers].mean(axis=1)

    benchmark_returns = {}

    benchmark_returns["SPY"] = returns[["SPY"]].mean(axis=1)

    if "QQQ" in returns.columns and "SMH" in returns.columns:
        benchmark_returns["Growth Strategy"] = returns[["QQQ", "SMH"]].dot([0.7, 0.3])

    alpha_names = [t for t in ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"] if t in returns.columns]
    if alpha_names:
        benchmark_returns["Concentrated Alpha"] = returns[alpha_names].mean(axis=1)

    if "SPY" in returns.columns and "TLT" in returns.columns:
        benchmark_returns["Defensive Allocation"] = returns[["SPY", "TLT"]].dot([0.6, 0.4])

    chart_df = pd.DataFrame({
        "Your Portfolio": portfolio_returns,
        **benchmark_returns
    }).dropna()

    growth = (1 + chart_df).cumprod() * 100

    return growth

@st.cache_data(show_spinner=False, ttl=900)
def calculate_portfolio_metrics(tickers, timeframe, custom_weights=None):
    period_map = {
        "1Y": "1y",
        "3Y": "3y",
        "5Y": "5y",
        "10Y": "10y",
    }

    period = period_map.get(timeframe, "5y")

    all_tickers = list(set(tickers + ["SPY"]))

    prices = yf.download(
        all_tickers,
        period=period,
        auto_adjust=True,
        progress=False
    )["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    prices = prices.dropna(axis=1, how="all").ffill().dropna()

    valid_tickers = [t for t in tickers if t in prices.columns]

    if not valid_tickers or "SPY" not in prices.columns:
        return None

    returns = prices.pct_change().dropna()

    if custom_weights:
        total = sum(custom_weights.values())
        norm_weights = {k: v / total for k, v in custom_weights.items()}

        portfolio_returns = sum(
            returns[ticker] * norm_weights.get(ticker, 0)
            for ticker in valid_tickers
        )
    else:
        portfolio_returns = returns[valid_tickers].mean(axis=1)
    spy_returns = returns["SPY"]

    annual_return = ((1 + portfolio_returns).prod() ** (252 / len(portfolio_returns)) - 1) * 100
    volatility = portfolio_returns.std() * np.sqrt(252) * 100

    cumulative = (1 + portfolio_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative / running_max - 1) * 100
    max_drawdown = drawdown.min()

    sharpe = annual_return / volatility if volatility != 0 else 0

    spy_annual_return = ((1 + spy_returns).prod() ** (252 / len(spy_returns)) - 1) * 100
    vs_spy = annual_return - spy_annual_return

    beta = portfolio_returns.cov(spy_returns) / spy_returns.var()

    if custom_weights:
        weights = {ticker: custom_weights.get(ticker, 0) for ticker in valid_tickers}
    else:
        weights = {ticker: round(100 / len(valid_tickers), 1) for ticker in valid_tickers}

    concentration = max(weights.values()) if weights else 0
    diversification_score = max(0, min(100, round(100 - concentration)))

    if volatility >= 25 or concentration >= 35:
        risk_level = "High"
    elif volatility >= 16:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "annual_return": annual_return,
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "spy_annual_return": spy_annual_return,
        "vs_spy": vs_spy,
        "beta": beta,
        "risk_level": risk_level,
        "diversification_score": diversification_score,
        "concentration": concentration,
        "weights": weights,
        "valid_tickers": valid_tickers,
    }

@st.cache_data(show_spinner=False, ttl=900)
def calculate_strategy_benchmark_metrics(tickers, timeframe):
    period_map = {
        "1Y": "1y",
        "3Y": "3y",
        "5Y": "5y",
        "10Y": "10y",
    }

    period = period_map.get(timeframe, "5y")

    strategies = {
        "Market Benchmark": ["SPY"],
        "Growth Strategy": ["QQQ", "SMH"],
        "Concentrated Alpha": ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"],
        "Defensive Allocation": ["SPY", "TLT"],
    }

    all_tickers = sorted(list(set(sum(strategies.values(), []))))

    prices = yf.download(
        all_tickers,
        period=period,
        auto_adjust=True,
        progress=False
    )["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    prices = prices.dropna(axis=1, how="all").ffill().dropna()
    returns = prices.pct_change().dropna()

    results = {}

    for name, basket in strategies.items():
        valid = [t for t in basket if t in returns.columns]

        if not valid:
            continue

        strategy_returns = returns[valid].mean(axis=1)

        annual_return = ((1 + strategy_returns).prod() ** (252 / len(strategy_returns)) - 1) * 100
        volatility = strategy_returns.std() * np.sqrt(252) * 100

        cumulative = (1 + strategy_returns).cumprod()
        drawdown = (cumulative / cumulative.cummax() - 1) * 100
        max_drawdown = drawdown.min()

        sharpe = annual_return / volatility if volatility != 0 else 0

        results[name] = {
            "annual_return": annual_return,
            "volatility": volatility,
            "max_drawdown": max_drawdown,
            "sharpe": sharpe,
            "holdings": " + ".join(valid)
        }

    return results

def benchmark_takeaway(title, bench_metrics, portfolio_metrics):
    if not bench_metrics or not portfolio_metrics:
        return "Benchmark read unavailable."

    br = bench_metrics["annual_return"]
    bv = bench_metrics["volatility"]
    bd = bench_metrics["max_drawdown"]

    pr = portfolio_metrics["annual_return"]
    pv = portfolio_metrics["volatility"]
    pd = portfolio_metrics["max_drawdown"]

    if title == "Market Benchmark":
        if pr > br and pv > bv:
            return "Beating SPY, but taking more heat."
        if pr > br:
            return "Clean market outperformance."
        return "SPY is still the hurdle."

    if title == "Growth Strategy":
        if abs(pr - br) < 3:
            return "Portfolio is tracking growth beta."
        if pr > br:
            return "Outrunning growth beta."
        return "Lagging growth despite similar risk."

    if title == "Concentrated Alpha":
        if abs(pr - br) < 3 and abs(pd - bd) < 5:
            return "Mega-cap tech in disguise."
        if pd > bd:
            return "Less fragile than pure mega-cap tech."
        return "Concentration risk is doing the work."

    if title == "Defensive Allocation":
        if pv > bv:
            return "You’re trading sleep for upside."
        return "Lower-volatility floor."

    return "Benchmark context loaded."

# -----------------------------
# Load base data
# -----------------------------
df = load_top_signals()

# -----------------------------
# Top header / controls
# -----------------------------
brand_col, input_col, button_col = st.columns([1.25, 3.6, 0.95], gap="medium")

with brand_col:
    st.markdown("<div style='margin-top:-4px;'>", unsafe_allow_html=True)
    st.image("assets/logo.png", width=230)
    st.markdown("</div>", unsafe_allow_html=True)



mode = st.radio(
    "",
    ["Stock Lens", "Portfolio Lab", "Allocation Engine"],
    horizontal=True,
    key="mode_toggle"
)

if mode == "Stock Lens":
    input_col, button_col = st.columns([4, 1], gap="medium")

    with input_col:
        typed_ticker = st.text_input(
            "",
            value=st.session_state.active_ticker or "",
            placeholder="Enter ticker (AAPL, NVDA, BTC-USD)",
            label_visibility="collapsed",
            key="stock_lens_ticker_input",
        ).strip().upper()

    with button_col:
        analyze_clicked = st.button(
            "Analyze",
            use_container_width=True,
            key="stock_lens_analyze_button",
        )

    if analyze_clicked and typed_ticker:
        st.session_state.active_ticker = typed_ticker
        st.rerun()

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)



active_ticker = st.session_state.active_ticker

if mode == "Stock Lens" and not active_ticker:
    welcome_html = (
        f'<div class="welcome-hero">'
            f'<div class="welcome-grid">'

                f'<div>'
                    f'<div class="welcome-pill">AI-POWERED MARKET INTELLIGENCE</div>'

                    f'<div class="welcome-title">'
                        f'Welcome to <span class="accent">AInvest</span>'
                    f'</div>'

                    f'<div class="welcome-subtitle">'
                        f'Get AI-powered market analysis, real-time signals, and institutional-grade insights '
                        f'for any stock or crypto.'
                    f'</div>'

                    f'<div class="welcome-features">'

                        f'<div class="welcome-feature">'
                            f'<div class="welcome-feature-icon">📈</div>'
                            f'<div>'
                                f'<div class="welcome-feature-title">Market Structure</div>'
                                f'<div class="welcome-feature-text">Real-time trend and structure</div>'
                            f'</div>'
                        f'</div>'

                        f'<div class="welcome-feature">'
                            f'<div class="welcome-feature-icon">📊</div>'
                            f'<div>'
                                f'<div class="welcome-feature-title">AI Signals</div>'
                                f'<div class="welcome-feature-text">AI-driven insights and alerts</div>'
                            f'</div>'
                        f'</div>'

                        f'<div class="welcome-feature">'
                            f'<div class="welcome-feature-icon">🛡️</div>'
                            f'<div>'
                                f'<div class="welcome-feature-title">Risk Analysis</div>'
                                f'<div class="welcome-feature-text">Conviction, risk level and key levels</div>'
                            f'</div>'
                        f'</div>'

                    f'</div>'
                f'</div>'

                f'<div class="welcome-art">'
                    f'<div class="welcome-bars">'
                        f'<div class="welcome-bar" style="height:12%"></div>'
                        f'<div class="welcome-bar" style="height:18%"></div>'
                        f'<div class="welcome-bar" style="height:22%"></div>'
                        f'<div class="welcome-bar" style="height:30%"></div>'
                        f'<div class="welcome-bar" style="height:26%"></div>'
                        f'<div class="welcome-bar" style="height:34%"></div>'
                        f'<div class="welcome-bar" style="height:40%"></div>'
                        f'<div class="welcome-bar" style="height:48%"></div>'
                        f'<div class="welcome-bar" style="height:60%"></div>'
                    f'</div>'
                f'</div>'

            f'</div>'
        f'</div>'
    )
    st.markdown(welcome_html, unsafe_allow_html=True)

    popular_html = (
        f'<div class="ticker-section">'
            f'<div class="ticker-section-title">Popular Tickers</div>'
            f'<div class="ticker-section-subtitle">Explore these active markets</div>'

            f'<div class="ticker-grid">'
                f'<div class="ticker-card">'
                    f'<div class="ticker-symbol">AAPL</div>'
                    f'<div class="ticker-name">Apple Inc.</div>'
                    f'<div class="ticker-price">$175.43</div>'
                    f'<div class="ticker-change-pos">+1.28%</div>'
                f'</div>'

                f'<div class="ticker-card">'
                    f'<div class="ticker-symbol">NVDA</div>'
                    f'<div class="ticker-name">NVIDIA Corp.</div>'
                    f'<div class="ticker-price">$932.17</div>'
                    f'<div class="ticker-change-pos">+2.14%</div>'
                f'</div>'

                f'<div class="ticker-card">'
                    f'<div class="ticker-symbol">TSLA</div>'
                    f'<div class="ticker-name">Tesla, Inc.</div>'
                    f'<div class="ticker-price">$168.22</div>'
                    f'<div class="ticker-change-neg">-0.73%</div>'
                f'</div>'

                f'<div class="ticker-card">'
                    f'<div class="ticker-symbol">MSFT</div>'
                    f'<div class="ticker-name">Microsoft Corp.</div>'
                    f'<div class="ticker-price">$420.15</div>'
                    f'<div class="ticker-change-pos">+0.91%</div>'
                f'</div>'

                f'<div class="ticker-card">'
                    f'<div class="ticker-symbol">BTC-USD</div>'
                    f'<div class="ticker-name">Bitcoin</div>'
                    f'<div class="ticker-price">$64,812.45</div>'
                    f'<div class="ticker-change-pos">+1.87%</div>'
                f'</div>'
            f'</div>'
        f'</div>'
    )
    st.markdown(popular_html, unsafe_allow_html=True)

    tip_html = (
        f'<div class="welcome-tip">'
            f'<div class="welcome-tip-icon">💡</div>'
            f'<div><b>Tip:</b> Enter any ticker above and click Analyze to launch the full dashboard.</div>'
        f'</div>'
    )
    st.markdown(tip_html, unsafe_allow_html=True)

# -----------------------------
# Main analyzed layout
# -----------------------------


if mode == "Stock Lens" and active_ticker:
    match = df[df["Ticker"] == active_ticker].copy()
    snapshot: dict[str, Any] = {"explanation_inputs": []}

    snapshot["company_name"] = active_ticker
    snapshot["ticker"] = active_ticker
    snapshot["explanation_inputs"].append(f"Ticker: {active_ticker}")

    latest_price = None
    daily_change_pct = None
    daily_change_dollar = None
    vs_ma20_pct = None
    hist = pd.DataFrame()
    headlines = []

    try:
        stock = yf.Ticker(active_ticker)
        hist = stock.history(period="1mo")
        headlines = fetch_recent_headlines(active_ticker)

        if not hist.empty and len(hist) >= 2:
            latest_price = round(float(hist["Close"].iloc[-1]), 2)
            prev_close = float(hist["Close"].iloc[-2])

            daily_change_dollar = round(latest_price - prev_close, 2)
            daily_change_pct = round(((latest_price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0

            ma20_series = hist["Close"].rolling(20).mean()
            if len(hist) >= 20 and not pd.isna(ma20_series.iloc[-1]):
                ma20 = float(ma20_series.iloc[-1])
                vs_ma20_pct = round(((latest_price - ma20) / ma20) * 100, 2)

            returns = hist["Close"].pct_change().dropna()
            volatility = float(np.std(returns) * (252 ** 0.5)) if not returns.empty else None

            snapshot["price"] = latest_price
            snapshot["change_pct"] = daily_change_pct
            snapshot["explanation_inputs"].append(f"Latest price: {latest_price}")
            snapshot["explanation_inputs"].append(f"Daily change %: {daily_change_pct}")
            snapshot["explanation_inputs"].append(f"Daily change $: {daily_change_dollar}")

            if vs_ma20_pct is not None:
                snapshot["explanation_inputs"].append(f"Vs MA20 %: {vs_ma20_pct}")
            if volatility is not None:
                snapshot["explanation_inputs"].append(f"Volatility: {round(volatility, 3)}")

    except Exception:
        hist = pd.DataFrame()

    if latest_price is None and hist.empty:
        st.error("Could not load data for that ticker. Try another symbol.")
    else:
        if not match.empty:
            stock_row = match.iloc[0]
            confidence = round(float(stock_row["Up Probability"]) * 100, 2)
            risk = get_model_risk(confidence)
            signal, color = get_signal(confidence)
            source_used = "Model signal + live market data"
        else:
            score = 50.0

            if daily_change_pct is not None:
                if daily_change_pct > 2:
                    score += 12
                elif daily_change_pct > 1:
                    score += 8
                elif daily_change_pct > 0:
                    score += 5
                elif daily_change_pct < -2:
                    score -= 12
                elif daily_change_pct < -1:
                    score -= 8
                elif daily_change_pct < 0:
                    score -= 5

            if vs_ma20_pct is not None:
                if vs_ma20_pct > 3:
                    score += 12
                elif vs_ma20_pct > 1:
                    score += 8
                elif vs_ma20_pct > 0:
                    score += 4
                elif vs_ma20_pct < -3:
                    score -= 12
                elif vs_ma20_pct < -1:
                    score -= 8
                elif vs_ma20_pct < 0:
                    score -= 4

            confidence = round(max(1.0, min(99.0, score)), 2)
            risk = get_fallback_risk(confidence)
            signal, color = get_signal(confidence)
            source_used = "Live market fallback"

        timeframe = st.radio(
            "Timeframe",
            ["Today", "5D", "1M", "3M", "1Y"],
            index=["Today", "5D", "1M", "3M", "1Y"].index(st.session_state.chart_timeframe),
            horizontal=True,
            label_visibility="collapsed",
            key="chart_timeframe",
        )

        if timeframe == "Today":
            chart_period = "1d"
            chart_interval = "5m"
        elif timeframe == "5D":
            chart_period = "5d"
            chart_interval = "15m"
        elif timeframe == "1M":
            chart_period = "1mo"
            chart_interval = "1d"
        elif timeframe == "3M":
            chart_period = "3mo"
            chart_interval = "1d"
        else:
            chart_period = "1y"
            chart_interval = "1d"

        chart_hist = yf.Ticker(active_ticker).history(
            period=chart_period,
            interval=chart_interval
        )

        chart_high = float(chart_hist["High"].tail(20).max()) if not chart_hist.empty and "High" in chart_hist else None
        chart_low = float(chart_hist["Low"].tail(20).min()) if not chart_hist.empty and "Low" in chart_hist else None

        vwap = None
        if not chart_hist.empty and {"High", "Low", "Close", "Volume"}.issubset(chart_hist.columns):
            typical = (chart_hist["High"] + chart_hist["Low"] + chart_hist["Close"]) / 3.0
            vol = chart_hist["Volume"].fillna(0)
            cum_vol = vol.cumsum()
            cum_pv = (typical * vol).cumsum()
            chart_hist["VWAP_TEMP"] = np.where(cum_vol > 0, cum_pv / cum_vol, np.nan)
            if not pd.isna(chart_hist["VWAP_TEMP"].iloc[-1]):
                vwap = float(chart_hist["VWAP_TEMP"].iloc[-1])

    current_time = time.time()

    if current_time - st.session_state.last_call < 5:
        ai_text = "AI insight paused briefly to prevent too many requests. Try again in a few seconds."
    else:
        st.session_state.last_call = current_time

        ai_text = generate_ai_explanation(
            ticker=active_ticker,
            confidence=confidence,
            risk=risk,
            source_used=source_used,
            latest_price=latest_price,
            daily_change_pct=daily_change_pct,
            headlines=tuple(headlines),
            extra_inputs=tuple(snapshot.get("explanation_inputs", [])),
        )

        ai_signal_summary = compact_ai_summary(
            latest_price=latest_price,
            daily_change_pct=daily_change_pct,
            vwap=vwap,
            high_level=chart_high,
            low_level=chart_low,
        )

        top_left, top_right = st.columns([2.05, 1.0], gap="medium")

        with top_left:
            if not chart_hist.empty:
                render_chart_module(
                    hist=chart_hist,
                    ticker=active_ticker,
                    signal=signal,
                    daily_change=daily_change_pct if daily_change_pct is not None else 0.0,
                    source_used=source_used,
                )

        with top_right:
            summary_html = (
                f'<div class="panel-card right-card" style="height:100%; display:flex; flex-direction:column; justify-content:space-between;">'
                f'<div>'
                f'<div class="summary-title">'
                f'<div class="summary-name">{active_ticker}</div>'
                f'<div class="signal-pill" style="background:{color};">{signal}</div>'
                f'</div>'

                f'<div class="metrics-2x2">'

                f'<div class="metric-tile">'
                f'<div class="metric-label">Conviction</div>'
                f'<div class="metric-value">{confidence:.2f}%</div>'
                f'</div>'

                f'<div class="metric-tile">'
                f'<div class="metric-label">Risk</div>'
                f'<div class="metric-value">{risk}</div>'
                f'</div>'

                f'<div class="metric-tile">'
                f'<div class="metric-label">Price</div>'
                f'<div class="metric-value">{f"${latest_price:.2f}" if latest_price is not None else "—"}</div>'
                f'</div>'

                f'<div class="metric-tile">'
                f'<div class="metric-label">Daily Change</div>'
                f'<div class="metric-value">{f"{daily_change_pct:+.2f}%" if daily_change_pct is not None else "—"}</div>'
                f'</div>'

                f'</div>'

                f'<div class="signal-summary">'
                f'<div class="signal-summary-title">AI Signal Summary</div>'
                f'<p>{ai_signal_summary.replace(chr(10), "<br>")}</p>'
                f'</div>'
                f'</div>'

                f'<div class="source-note">Source: {source_used}</div>'
                f'</div>'
            )
            st.markdown(summary_html, unsafe_allow_html=True)

        bottom_left, bottom_right = st.columns([1.0, 1.0], gap="medium")

        with bottom_left:
            insight_html = (
                f'<div class="bottom-card">'
                f'<div class="card-heading">'
                f'<div class="card-title">AI Trader Insight</div>'
                f'</div>'

                f'<div class="card-body">'
                f'{ai_text.replace(chr(10), "<br>")}'
                f'</div>'

                f'</div>'
            )
            st.markdown(insight_html, unsafe_allow_html=True)

        with bottom_right:
            if headlines:
                news_items = "".join([
                    f'<div class="headline-row">'
                    f'<div class="headline-title">{h}</div>'
                    f'</div>'
                    for h in headlines
                ])
            else:
                news_items = '<div class="headline-title">No recent headlines</div>'

            news_html = (
                f'<div class="bottom-card">'
                f'<div class="card-heading">'
                f'<div class="card-title">Latest Headlines</div>'
                f'</div>'

                f'<div class="card-body">'
                f'{news_items}'
                f'</div>'

                f'</div>'
            )
            st.markdown(news_html, unsafe_allow_html=True)

        st.markdown(
            """
            <div class="footer-note">
                All analysis is for informational purposes only and not financial advice.
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    
   
if "Portfolio" in str(mode):
    st.markdown("## Portfolio Lab")

    if "portfolio_tickers" not in st.session_state:
        st.session_state.portfolio_tickers = []

    if "portfolio_weight_mode" not in st.session_state:
        st.session_state.portfolio_weight_mode = "Equal Weight"

    if "portfolio_analyzed" not in st.session_state:
        st.session_state.portfolio_analyzed = False

    if "portfolio_timeframe" not in st.session_state:
        st.session_state.portfolio_timeframe = "5Y"

    if st.session_state.get("clear_portfolio_new_ticker", False):
        st.session_state.portfolio_new_ticker = ""
        st.session_state.clear_portfolio_new_ticker = False

    portfolio_ready = len(st.session_state.portfolio_tickers) >= 2
    

    portfolio_ready = len(st.session_state.portfolio_tickers) >= 2

    portfolio_metrics = None

    strategy_metrics = None

    main_col, right_col = st.columns([3, 1], gap="medium")

    with main_col:
        build_col, outlook_col = st.columns([1, 2.1], gap="medium")

        # -----------------------------
        # Build Panel (FIXED HEIGHT)
        # -----------------------------
        with build_col:
            build_box = st.container(height=390)

            with build_box:
                st.markdown("### Build Your Portfolio")
                st.caption("Add 2+ stocks to analyze performance vs benchmarks")

                chip_cols = st.columns(4)
                for i, ticker in enumerate(st.session_state.portfolio_tickers):
                    with chip_cols[i % 4]:
                        if st.button(f"{ticker} ×", key=f"remove_{ticker}", use_container_width=True):
                            st.session_state.portfolio_tickers.remove(ticker)
                            st.rerun()

                add_col, button_col = st.columns([4, 1])

                with add_col:
                    new_ticker = st.text_input(
                        "",
                        placeholder="Add ticker",
                        key="portfolio_new_ticker",
                        label_visibility="collapsed"
                    )

                if len(st.session_state.portfolio_tickers) == 0:
                    st.caption("Enter ticker symbols, not company names. Examples: MSFT, GM, AAPL, SPY, BTC-USD.")

                if len(st.session_state.portfolio_tickers) == 1:
                    st.caption("Add at least 2 tickers to analyze a portfolio.")

                with button_col:
                    if st.button("+ Add", key="portfolio_add_ticker", use_container_width=True):
                        ticker = new_ticker.strip().upper()
                        if ticker and ticker not in st.session_state.portfolio_tickers:
                            st.session_state.portfolio_tickers.append(ticker)
                            st.session_state.clear_portfolio_new_ticker = True
                            st.rerun()

                st.markdown("**Weighting**")

                weight_col1, weight_col2 = st.columns(2)

                with weight_col1:
                    if st.button(
                        "Equal Weight",
                        key="portfolio_equal_weight",
                        use_container_width=True,
                        type="primary" if st.session_state.portfolio_weight_mode == "Equal Weight" else "secondary"
                    ):
                        st.session_state.portfolio_weight_mode = "Equal Weight"
                        st.rerun()

                with weight_col2:
                    if st.button(
                        "Custom Weights",
                        key="portfolio_custom_weights",
                        use_container_width=True,
                        type="primary" if st.session_state.portfolio_weight_mode == "Custom Weights" else "secondary"
                    ):
                        st.session_state.portfolio_weight_mode = "Custom Weights"
                        st.rerun()

                       # AFTER Equal Weight + Custom Weight buttons
                    active_weights = None

                    if st.session_state.portfolio_weight_mode == "Custom Weights":
                        st.markdown("**Set target weights**")

                        custom_weights = {}

                        cols = st.columns(2)

                        for i, ticker in enumerate(st.session_state.portfolio_tickers):
                            with cols[i % 2]:
                                custom_weights[ticker] = st.number_input(
                                    f"{ticker} %",
                                    min_value=0,
                                    max_value=100,
                                    value=round(100 / len(st.session_state.portfolio_tickers)),
                                    step=1,
                                    key=f"weight_{ticker}",
                                )

                        total = sum(custom_weights.values())
                        st.caption(f"Total weight: {total}%")

                        if total != 100:
                            st.warning("Total weight must equal 100%")

                        

                        

                        
                                            

                    if portfolio_ready:
                        st.caption("Portfolio updates automatically as tickers and weights change.")
                    else:
                        st.caption("Add at least 2 tickers to analyze a portfolio.")

                        st.caption(f"{len(st.session_state.portfolio_tickers)} assets • {st.session_state.portfolio_weight_mode}")

            # -----------------------------
            # ALWAYS CALCULATE (Fix)
            # -----------------------------
            active_weights = None

            if st.session_state.portfolio_weight_mode == "Custom Weights":
                active_weights = {
                    ticker: st.session_state.get(f"weight_{ticker}", 0)
                    for ticker in st.session_state.portfolio_tickers
                }

            portfolio_metrics = calculate_portfolio_metrics(
                st.session_state.portfolio_tickers,
                st.session_state.portfolio_timeframe,
                active_weights
            ) if portfolio_ready else None

            strategy_metrics = calculate_strategy_benchmark_metrics(
                st.session_state.portfolio_tickers,
                st.session_state.portfolio_timeframe
            ) if portfolio_ready else None

        # -----------------------------
        # Outlook + Stress Scenarios
        # -----------------------------
        with outlook_col:
            title_col, time_col = st.columns([3, 2])

            with title_col:
                st.markdown("### Portfolio Outlook")

            with time_col:
                time_cols = st.columns(4)
                for i, tf in enumerate(["1Y", "3Y", "5Y", "10Y"]):
                    with time_cols[i]:
                        if st.button(
                            tf,
                            key=f"portfolio_timeframe_{tf}",
                            use_container_width=True,
                            type="primary" if st.session_state.portfolio_timeframe == tf else "secondary"
                        ):
                            st.session_state.portfolio_timeframe = tf
                            st.rerun()

            metric_cols = st.columns(5)

            labels = [
                "Annualized Return",
                "Volatility",
                "Max Drawdown",
                "Sharpe Ratio",
                "Vs. S&P 500"
            ]

            metric_values = ["—", "—", "—", "—", "—"]

            if portfolio_metrics:
                metric_values = [
                    f"{portfolio_metrics['annual_return']:.2f}%",
                    f"{portfolio_metrics['volatility']:.2f}%",
                    f"{portfolio_metrics['max_drawdown']:.2f}%",
                    f"{portfolio_metrics['sharpe']:.2f}",
                    f"{portfolio_metrics['vs_spy']:+.2f}%"
                ]

            for i, label in enumerate(labels):
                with metric_cols[i]:
                    st.caption(label)
                    st.markdown(f"### {metric_values[i]}")

           
            # -----------------------------
            # Stress Scenarios (NEW FEATURE)
            # -----------------------------
            st.markdown("### Stress Scenarios")
            st.caption("Estimated 1-day portfolio impact under key market moves")

            scenario_cols = st.columns(4)

            scenarios = [
                ("Market -2%", "-3.1%", "#FF4D6D"),
                ("Tech Selloff", "-4.8%", "#FF4D6D"),
                ("Rates Spike", "-1.6%", "#FFB020"),
                ("Risk-On Rally", "+3.9%", "#2EE59D"),
            ]

            for i, (name, impact, color) in enumerate(scenarios):
                with scenario_cols[i]:

                    bg = get_stress_bg(color)

                    st.markdown(
                        f"""
                        <div class="portfolio-card" style="padding:10px; min-height:72px; background:{bg}; border:1px solid rgba(255,255,255,0.08);">
                            <div style="font-size:0.72rem; color:rgba(231,238,249,0.70);">{name}</div>
                            <div style="font-size:1.25rem; font-weight:800; color:{color}; margin-top:4px;">{impact}</div>
                            <div style="font-size:0.66rem; color:rgba(231,238,249,0.55);">Impact</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # -----------------------------
        # CHART
        # -----------------------------
        st.markdown("### Portfolio vs Benchmarks")

        try:
            chart_data = build_portfolio_benchmark_chart(
                st.session_state.portfolio_tickers,
                st.session_state.portfolio_timeframe
            )

            fig = go.Figure()

            colors = {
                "Your Portfolio": "#3A8DFF",
                "SPY": "rgba(255,255,255,0.65)",
                "Growth Strategy": "#2EE59D",
                "Concentrated Alpha": "#9B5CF6",
                "Defensive Allocation": "#F59E0B",
            }

            for col in chart_data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=chart_data.index,
                        y=chart_data[col],
                        mode="lines",
                        name=col,
                        line=dict(
                            color=colors.get(col),
                            width=3 if col == "Your Portfolio" else 1.6
                        )
                    )
                )

            fig.update_layout(
                height=390,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E7EEF9"),
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(
                    orientation="h",
                    y=1.05,
                    x=0,
                    font=dict(size=13, color="#FFFFFF"),
                    bgcolor="rgba(0,0,0,0.35)"
                ),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(
                    gridcolor="rgba(255,255,255,0.06)",
                    title="Growth of $100"
                ),
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception:
            st.info("Chart will appear once data loads.")

        # -----------------------------
        # STRATEGY BENCHMARKS
        # -----------------------------
        st.markdown("### Strategy Benchmarks")

        bench_cols = st.columns(4)

        benchmark_cards = [
                ("Market Benchmark", "SPY", "Did you beat the market?"),
                ("Growth Strategy", "QQQ + SMH", "Checks tech-beta exposure."),
                ("Concentrated Alpha", "Mega-cap tech", "Tests concentration risk."),
                ("Defensive Allocation", "SPY + TLT", "Shows lower-risk alternative."),
            ]

        for i, (title, subtitle, _) in enumerate(benchmark_cards):
            with bench_cols[i]:
                metrics = strategy_metrics.get(title) if strategy_metrics else None
                takeaway = benchmark_takeaway(title, metrics, portfolio_metrics)

                if metrics:
                    card_body = (
                        f'<div style="display:flex; justify-content:space-between; margin-top:8px;">'
                        f'<span>Return</span><span>{metrics["annual_return"]:.2f}%</span>'
                        f'</div>'
                        f'<div style="display:flex; justify-content:space-between;">'
                        f'<span>Volatility</span><span>{metrics["volatility"]:.2f}%</span>'
                        f'</div>'
                        f'<div style="display:flex; justify-content:space-between;">'
                        f'<span>Max Drawdown</span><span>{metrics["max_drawdown"]:.2f}%</span>'
                        f'</div>'
                        f'<div style="display:flex; justify-content:space-between;">'
                        f'<span>Sharpe</span><span>{metrics["sharpe"]:.2f}</span>'
                        f'</div>'
                    )
                else:
                    card_body = (
                        f'<div class="portfolio-placeholder">Metrics unavailable.</div>'
                    )

                benchmark_card = (
                    f'<div class="portfolio-card">'
                    f'<h3>{title}</h3>'
                    f'<div class="portfolio-subtext">{subtitle}</div>'
                    f'{card_body}'
                    f'<div style="margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.08); color:#73CFFF; font-size:0.78rem; font-weight:700;">'
                    f'{takeaway}'
                    f'</div>'
                    f'</div>'
                )

                st.markdown(benchmark_card, unsafe_allow_html=True)

    # -----------------------------
    # RIGHT PANEL
    # -----------------------------
    with right_col:
        st.markdown("### Risk Profile")

        risk_color = "#FF4D6D"

        if portfolio_metrics:
            if portfolio_metrics["risk_level"] == "Low":
                risk_color = "#2EE59D"
            elif portfolio_metrics["risk_level"] == "Medium":
                risk_color = "#FFB020"

        st.markdown(
            f"""
            <div class="portfolio-card" style="padding:16px; text-align:center;">
                <div style="color:rgba(231,238,249,0.7); font-size:0.9rem;">Risk Level</div>
                <div style="margin-top:8px; font-size:1.4rem; font-weight:700; color:{risk_color};">{portfolio_metrics['risk_level'] if portfolio_metrics else "—"}</div>
                <div style="margin-top:12px; height:8px; border-radius:6px; background:linear-gradient(90deg,#2EE59D,#FFB020,#FF4D6D); opacity:0.4;"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="portfolio-card" style="margin-top:10px;">
                <div style="display:flex; justify-content:space-between;"><span>Volatility ({st.session_state.portfolio_timeframe})</span><span>{f"{portfolio_metrics['volatility']:.2f}%" if portfolio_metrics else "—"}</span></div>
                <div style="display:flex; justify-content:space-between;"><span>Beta vs S&P 500</span><span>{f"{portfolio_metrics['beta']:.2f}" if portfolio_metrics else "—"}</span></div>
                <div style="display:flex; justify-content:space-between;"><span>Diversification Score</span><span>{portfolio_metrics['diversification_score'] if portfolio_metrics else "—"}</span></div>
                <div style="display:flex; justify-content:space-between;"><span>Concentration Risk</span><span>{f"{portfolio_metrics['concentration']:.1f}%" if portfolio_metrics else "—"}</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        top_holdings_html = ""

        if portfolio_metrics and portfolio_metrics["weights"]:
            top_holdings = sorted(
                portfolio_metrics["weights"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            for ticker, weight in top_holdings:
                top_holdings_html += (
                    f'<div style="display:flex; justify-content:space-between;">'
                    f'<span>{ticker}</span>'
                    f'<span>{weight:.1f}%</span>'
                    f'</div>'
                )
        else:
            top_holdings_html = (
                f'<div style="display:flex; justify-content:space-between;"><span>—</span><span>—</span></div>'
                f'<div style="display:flex; justify-content:space-between;"><span>—</span><span>—</span></div>'
                f'<div style="display:flex; justify-content:space-between;"><span>—</span><span>—</span></div>'
            )

        top_holdings_card = (
            f'<div class="portfolio-card" style="margin-top:10px;">'
            f'<div style="font-weight:700; margin-bottom:8px;">Top 3 Holdings</div>'
            f'{top_holdings_html}'
            f'</div>'
        )

        st.markdown(top_holdings_card, unsafe_allow_html=True)

        st.markdown("### Portfolio Composition")

        if portfolio_metrics and portfolio_metrics["weights"]:
            labels = list(portfolio_metrics["weights"].keys())
            values = list(portfolio_metrics["weights"].values())

            fig_comp = go.Figure(
                data=[
                    go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.58,
                        textinfo="percent",
                        textfont=dict(size=11),
                        hoverinfo="label+percent",
                        marker=dict(
                            colors=[
                                "#3A8DFF",  # blue
                                "#2EE59D",  # green
                                "#FF4D6D",  # red
                                "#9B5CF6",  # purple
                                "#F59E0B",  # amber
                            ]
                        )
                     )  
                ]  
            )

            fig_comp.update_layout(
                height=240,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E7EEF9", size=11),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    y=-0.15,
                    font=dict(size=10, color="#E7EEF9"),
                )
            )

            st.plotly_chart(fig_comp, width="stretch")

        else:
            composition_card = (
                f'<div class="portfolio-placeholder medium">'
                f'Portfolio composition will appear once data loads.'
                f'</div>'
            )
            st.markdown(composition_card, unsafe_allow_html=True)

        portfolio_brief = generate_portfolio_brief(
            st.session_state.portfolio_tickers,
            portfolio_metrics,
            st.session_state.portfolio_timeframe
        )

        portfolio_brief_card = (
            f'<div class="bottom-card" style="margin-top:10px;">'
            f'<div class="card-heading">'
            f'<div class="card-title">AI Portfolio Brief</div>'
            f'</div>'
            f'<div class="card-body" style="font-size:0.9rem; line-height:1.55;">'
            f'{portfolio_brief.replace(chr(10), "<br>")}'
            f'</div>'
            f'</div>'
        )

        st.markdown(portfolio_brief_card, unsafe_allow_html=True)

if mode == "Allocation Engine":
    st.markdown("## Allocation Engine")

    st.markdown("### Build Your Portfolio")
    st.caption("Construct a portfolio based on risk and time horizon")

    st.info("Allocation Engine coming next...")