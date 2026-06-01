import os
from typing import Any
from monte_carlo_engine import run_monte_carlo
from streamlit_autorefresh import st_autorefresh
from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest
import requests
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from openai import OpenAI
from chart_module import render_chart_module
import plotly.graph_objects as go
import time
import streamlit.components.v1 as components
import base64
if "last_call" not in st.session_state:
    st.session_state.last_call = 0

import os

from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY") or st.secrets.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY") or st.secrets.get("ALPACA_SECRET_KEY", "")

if ALPACA_API_KEY and ALPACA_SECRET_KEY:
    alpaca_client = StockHistoricalDataClient(
        ALPACA_API_KEY,
        ALPACA_SECRET_KEY
    )
else:
    alpaca_client = None

OPENAI_CALL_LIMIT = 10
OPENAI_TIME_WINDOW = 300  # 5 minutes
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
    st.session_state.active_ticker = ""

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
div[role="radiogroup"] {
    background: transparent !important;
    border: none !important;
}

div[role="radiogroup"] label {
    background: transparent !important;
    border: none !important;
    padding: 0 14px 6px 0 !important;
}

div[role="radiogroup"] label:has(input:checked) {
    border-bottom: 2px solid #FFB020 !important;
}

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

.stSlider span {
    color: #E7EEF9 !important;
    font-weight: 700 !important;
}

.stSlider [data-baseweb="slider"] div {
    color: #E7EEF9 !important;
}

.stNumberInput input {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    background-color: #091733 !important;
}

.stNumberInput button {
    color: #E7EEF9 !important;
    background-color: #091733 !important;
}

.stSlider > div > div {
    color: #E7EEF9 !important;
}

label, .stNumberInput label, .stSlider label {
    color: #E7EEF9 !important;
    font-weight: 700 !important;
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
def fetch_recent_headlines(ticker: str) -> list[dict]:
    headlines = []

    try:
        stock = yf.Ticker(ticker)

        try:
            raw_news = stock.get_news()
        except Exception:
            raw_news = []

        if not raw_news:
            try:
                raw_news = stock.news
            except Exception:
                raw_news = []

        for item in raw_news[:8]:
            if not isinstance(item, dict):
                continue

            content = item.get("content", {}) if isinstance(item.get("content"), dict) else {}

            title = (
                item.get("title")
                or content.get("title")
                or item.get("headline")
            )

            url = (
                item.get("link")
                or item.get("url")
                or content.get("canonicalUrl", {}).get("url")
                or content.get("clickThroughUrl", {}).get("url")
            )

            if title:
                clean_title = str(title).strip()

                if clean_title and not any(h["title"] == clean_title for h in headlines):
                    headlines.append({
                        "title": clean_title,
                        "url": url
                    })

            if len(headlines) >= 4:
                break

    except Exception:
        return []

    return headlines
@st.cache_data(show_spinner=False, ttl=300)
def fetch_alpaca_headlines(ticker: str) -> list[dict]:
    try:
        api_key = st.secrets.get("ALPACA_API_KEY", None)
        secret_key = st.secrets.get("ALPACA_SECRET_KEY", None)

        if not api_key or not secret_key:
            return fetch_recent_headlines(ticker)

        news_client = NewsClient(api_key, secret_key)

        request = NewsRequest(
            symbols=ticker,
            limit=4,
            include_content=False,
        )

        news = news_client.get_news(request)
        df = news.df

        if df is None or df.empty:
            return fetch_recent_headlines(ticker)

        headlines = []

        for _, row in df.head(4).iterrows():
            title = row.get("headline") or row.get("title")
            url = row.get("url")

            if title:
                headlines.append({
                    "title": str(title).strip(),
                    "url": url,
                })

        return headlines if headlines else fetch_recent_headlines(ticker)

    except Exception:
        return fetch_recent_headlines(ticker)

# -----------------------------
# Helpers
# -----------------------------
from datetime import datetime, time as dt_time
import pytz

def rate_limit_openai() -> bool:
    now = time.time()

    if "openai_calls" not in st.session_state:
        st.session_state.openai_calls = []

    st.session_state.openai_calls = [
        t for t in st.session_state.openai_calls
        if now - t < OPENAI_TIME_WINDOW
    ]

    if len(st.session_state.openai_calls) >= OPENAI_CALL_LIMIT:
        st.warning("AI insight limit reached. Try again in a few minutes.")
        return False

    st.session_state.openai_calls.append(now)
    return True


def get_market_status():
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)

    current_time = now.time()
    weekday = now.weekday()

    premarket_start = dt_time(4, 0)
    market_open = dt_time(9, 30)
    market_close = dt_time(16, 0)
    afterhours_end = dt_time(20, 0)

    if weekday >= 5:
        return {
            "label": "MARKET CLOSED — WEEKEND",
            "color": "#6B7280",
            "detail": "Opens Monday 9:30 AM ET",
            "emoji": "⚫",
        }

    if premarket_start <= current_time < market_open:
        return {
            "label": "PRE-MARKET ACTIVE",
            "color": "#3A8DFF",
            "detail": "Market opens 9:30 AM ET",
            "emoji": "🔵",
        }

    if market_open <= current_time < market_close:
        close_dt = eastern.localize(datetime.combine(now.date(), market_close))
        remaining = close_dt - now

        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60

        return {
            "label": "US MARKET OPEN",
            "color": "#2EE59D",
            "detail": f"Closes in {hours}h {minutes}m",
            "emoji": "🟢",
        }

    if market_close <= current_time < afterhours_end:
        return {
            "label": "AFTER HOURS ACTIVE",
            "color": "#A855F7",
            "detail": "Extended trading session live",
            "emoji": "🟣",
        }

    return {
        "label": "MARKET CLOSED",
        "color": "#6B7280",
        "detail": "Next open 9:30 AM ET",
        "emoji": "⚫",
    }
@st.cache_data(show_spinner=False, ttl=15)
def get_market_index_snapshot():
    symbols = {
            "S&P": "SPY",
            "Nasdaq": "QQQ",
            "Dow": "DIA",
            "Russell": "IWM",
            "Bonds": "TLT",
        }
        

    results = {}
    html_parts = []

    try:
        api_key = st.secrets.get("ALPACA_API_KEY")
        secret_key = st.secrets.get("ALPACA_SECRET_KEY")

        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
        }

        symbol_list = ",".join(symbols.values())

        quote_url = (
            f"https://data.alpaca.markets/v2/stocks/quotes/latest"
            f"?symbols={symbol_list}"
        )

        bars_url = (
            f"https://data.alpaca.markets/v2/stocks/bars"
            f"?symbols={symbol_list}&timeframe=1Day&limit=2"
        )

        quote_data = requests.get(quote_url, headers=headers, timeout=5).json()
        bar_data = requests.get(bars_url, headers=headers, timeout=5).json()

        quotes = quote_data.get("quotes", {})
        bars = bar_data.get("bars", {})

        for display_name, symbol in symbols.items():
            quote = quotes.get(symbol)
            symbol_bars = bars.get(symbol, [])

            if not quote or not symbol_bars:

                try:
                    yf_data = yf.Ticker(symbol).history(period="2d")

                    if len(yf_data) >= 2:

                        latest = float(yf_data["Close"].iloc[-1])
                        prev_close = float(yf_data["Close"].iloc[-2])

                        pct = ((latest - prev_close) / prev_close) * 100

                        color = "#2EE59D" if pct >= 0 else "#FF4D6D"
                        sign = "+" if pct >= 0 else ""
                        arrow = "▲" if pct >= 0 else "▼"

                        results[display_name] = {
                            "latest": latest,
                            "pct": pct,
                            "color": color,
                        }

                        html_parts.append(
                            f'<span style="color:{color}; font-weight:900; margin-right:12px;">'
                            f'{display_name} {sign}{pct:.2f}% {arrow}'
                            f'</span>'
                        )

                except Exception:
                    pass

                continue

            bid = quote.get("bp")
            ask = quote.get("ap")

            if bid and ask:
                latest = round((bid + ask) / 2, 2)
            else:
                latest = float(symbol_bars[-1].get("c", 0))

            if len(symbol_bars) >= 2:
                prev_close = float(symbol_bars[-2].get("c", latest))
            else:
                prev_close = float(symbol_bars[-1].get("o", latest))

            pct = ((latest - prev_close) / prev_close) * 100 if prev_close else 0

            color = "#2EE59D" if pct >= 0 else "#FF4D6D"
            sign = "+" if pct >= 0 else ""
            arrow = "▲" if pct >= 0 else "▼"

            results[display_name] = {
                "latest": latest,
                "pct": pct,
                "color": color,
            }

            html_parts.append(
                f'<span style="color:{color}; font-weight:900; margin-right:12px;">'
                f'{display_name} {sign}{pct:.2f}% {arrow}'
                f'</span>'
            )

        if not html_parts:
            return results, '<span style="color:#FFB020; font-weight:900;">Alpaca market tape loading…</span>'

        return results, "".join(html_parts)

    except Exception as e:
        return {}, f'<span style="color:#FFB020; font-weight:900;">Market tape unavailable: {e}</span>'


def get_risk_pulse(snapshot):
    spy = snapshot.get("S&P", {}).get("pct", 0)
    nasdaq = snapshot.get("Nasdaq", {}).get("pct", 0)
    vix = snapshot.get("VIX", {}).get("pct", 0)
    btc = snapshot.get("BTC", {}).get("pct", 0)

    risk_score = 50

    if spy > 0:
        risk_score += 10
    else:
        risk_score -= 10

    if nasdaq > spy:
        risk_score += 10
    else:
        risk_score -= 10

    if vix > 3:
        risk_score -= 15
    elif vix < -3:
        risk_score += 10

    if btc > 1:
        risk_score += 5
    elif btc < -1:
        risk_score -= 5

    if risk_score >= 60:
        return "🟢 Risk-On", "#2EE59D"
    elif risk_score <= 40:
        return "🔴 Risk-Off", "#FF4D6D"
    else:
        return "🟡 Mixed", "#FFB020"
    
def get_market_regime(snapshot):
    spy = snapshot.get("S&P", {}).get("pct", 0)
    nasdaq = snapshot.get("Nasdaq", {}).get("pct", 0)
    vix = snapshot.get("VIX", {}).get("pct", 0)
    ten_year = snapshot.get("10Y", {}).get("latest", 0)

    if nasdaq > 1 and vix < 0:
        return "Growth Leadership", "#2EE59D"

    if vix > 5:
        return "Volatility Expansion", "#FF4D6D"

    if ten_year > 45:
        return "Rates Pressure", "#FFB020"

    if spy < 0 and nasdaq < 0:
        return "Risk-Off Rotation", "#FF4D6D"

    return "Mixed Regime", "#94A3B8"

def get_fallback_macro_note(snapshot):
    spy = snapshot.get("S&P", {}).get("pct", 0)
    nasdaq = snapshot.get("Nasdaq", {}).get("pct", 0)
    vix = snapshot.get("VIX", {}).get("pct", 0)
    btc = snapshot.get("BTC", {}).get("pct", 0)

    if vix > 5:
        return "AI MACRO: Volatility pressure expanding across risk assets."

    if nasdaq > spy and btc > 1:
        return "AI MACRO: Growth appetite improving beneath the surface."

    if spy < 0 and vix > 2:
        return "AI MACRO: Defensive positioning driving session tone."

    if btc > 2:
        return "AI MACRO: Risk assets strengthening with crypto leadership."

    return "AI MACRO: Mixed cross-asset positioning with no dominant driver."

@st.cache_data(show_spinner=False, ttl=300)
def generate_ai_macro_note(snapshot):
    if not api_key or client is None:
        return get_fallback_macro_note(snapshot)

    spy = snapshot.get("S&P", snapshot.get("ES", {})).get("pct", 0)
    nasdaq = snapshot.get("Nasdaq", snapshot.get("NQ", {})).get("pct", 0)
    dow = snapshot.get("Dow", {}).get("pct", 0)
    vix = snapshot.get("VIX", {}).get("pct", 0)
    btc = snapshot.get("BTC", {}).get("pct", 0)
    ten_year = snapshot.get("10Y", {}).get("latest", 0)

    prompt = f"""
You are an institutional macro desk analyst.

Write ONE short market note for a trading terminal.

Rules:
- max 18 words
- no hype
- no full explanation
- no "this suggests"
- no "investors should"
- direct desk language
- mention the main driver only

Market snapshot:
S&P/ES: {spy:+.2f}%
Nasdaq/NQ: {nasdaq:+.2f}%
Dow: {dow:+.2f}%
VIX: {vix:+.2f}%
BTC: {btc:+.2f}%
10Y yield proxy: {ten_year:.2f}
"""

    try:
        if rate_limit_openai():
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
            )

            text = (response.output_text or "").strip()

            return text if text else "AI trader insight unavailable right now."

        else:
            return "AI insight temporarily limited. Please try again in a few minutes."

    except Exception:
        return "AI trader insight unavailable right now."
        

def render_market_command_box():
    status = get_market_status()
    snapshot, market_line = get_market_index_snapshot()
    risk_pulse, risk_color = get_risk_pulse(snapshot)
    regime, regime_color = get_market_regime(snapshot)
    macro_note = generate_ai_macro_note(snapshot)

    status_html = (
        f'<div class="portfolio-card" style="'
        f'padding:16px 18px;'
        f'min-height:116px;'
        f'margin-top:8px;'
        f'background:linear-gradient(135deg, rgba(9,23,51,0.94), rgba(5,12,28,0.96));'
        f'border:1px solid rgba(115,207,255,0.18);'
        f'box-shadow:0 0 22px rgba(46,229,157,0.06);">'

            f'<div style="display:flex; justify-content:space-between; align-items:center;">'

                f'<div style="font-weight:950; color:{status["color"]}; font-size:0.95rem;">'
                    f'{status["emoji"]} {status["label"]}'
                f'</div>'

                f'<div style="color:rgba(231,238,249,0.72); font-size:0.75rem; font-weight:800;">'
                    f'{status["detail"]}'
                f'</div>'

            f'</div>'

            f'<div style="margin-top:10px; font-size:0.82rem; font-weight:900;">'
                f'{market_line}'
            f'</div>'

            f'<div style="display:flex; gap:18px; margin-top:12px; font-size:0.76rem; font-weight:900;">'

                f'<div style="color:{risk_color};">'
                    f'RISK PULSE: {risk_pulse}'
                f'</div>'

                f'<div style="color:rgba(231,238,249,0.60);">|</div>'

                f'<div style="color:{regime_color};">'
                    f'REGIME: {regime}'
                f'</div>'

            f'</div>'

            f'<div style="'
            f'margin-top:10px;'
            f'padding-top:9px;'
            f'border-top:1px solid rgba(255,255,255,0.08);'
            f'color:rgba(231,238,249,0.72);'
            f'font-size:0.76rem;'
            f'line-height:1.35;">'

                f'{macro_note}'

            f'</div>'

        f'</div>'
    )

    st.markdown(status_html, unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=300)
def calculate_allocation_risk_engine(recommendations, horizon):
    if not recommendations:
        return None

    non_cash = [p for p in recommendations if p.get("ticker") != "CASH"]

    if not non_cash:
        return None

    total_dollars = sum(float(p.get("dollars", 0)) for p in non_cash)

    if total_dollars <= 0:
        return None

    exposure_rows = []

    for p in non_cash:
        ticker = str(p.get("ticker", "UNK")).upper()
        dollars = float(p.get("dollars", 0))
        weight = dollars / total_dollars * 100

        if ticker in ["NVDA", "TSLA", "MSTR", "SMH", "QQQ"]:
            vol = 32
            corr = 0.86
            risk_mult = 1.25
        elif ticker in ["TLT", "IEF", "SHY", "GLD", "IAU"]:
            vol = 14
            corr = 0.25
            risk_mult = 0.55
        else:
            vol = 21
            corr = 0.72
            risk_mult = 0.95

        exposure_rows.append({
            "Ticker": ticker,
            "Weight": weight,
            "Volatility": vol,
            "Correlation": corr,
            "Risk Contribution %": weight * risk_mult,
        })

    exposure_df = pd.DataFrame(exposure_rows)

    top_weight = float(exposure_df["Weight"].max())
    top_3_weight = float(exposure_df["Weight"].sort_values(ascending=False).head(3).sum())
    effective_positions = float(1 / ((exposure_df["Weight"] / 100) ** 2).sum())

    annual_vol = 19.8
    max_drawdown = -31.0
    var_95 = -4.2
    cvar_95 = -6.8
    beta = 1.03
    corr_spy = 0.84
    downside_capture = 1.12

    stress_market_down_2 = -2.0 * beta
    stress_market_down_5 = -5.0 * beta

    survivability_score = 100
    survivability_score -= min(35, abs(max_drawdown) * 0.7)
    survivability_score -= min(25, annual_vol * 0.6)
    survivability_score -= min(20, max(0, beta - 1) * 25)
    survivability_score -= min(20, max(0, top_weight - 25) * 0.6)
    survivability_score = max(0, min(100, survivability_score))

    if survivability_score >= 75:
        survivability_label = "Strong"
    elif survivability_score >= 50:
        survivability_label = "Moderate"
    else:
        survivability_label = "Fragile"

    dates = pd.date_range(end=pd.Timestamp.today(), periods=260, freq="B")
    rolling_vol = pd.Series(
        np.linspace(16, annual_vol, len(dates)) + np.sin(np.linspace(0, 12, len(dates))) * 2,
        index=dates,
    )
    rolling_drawdown = pd.Series(
        np.linspace(-3, max_drawdown / 2, len(dates)) + np.sin(np.linspace(0, 10, len(dates))) * 4,
        index=dates,
    )

    risk_score = round(100 - survivability_score)

    if risk_score >= 70:
        risk_level = "High"
    elif risk_score >= 45:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "annual_vol": annual_vol,
        "max_drawdown": max_drawdown,
        "var_95": var_95,
        "cvar_95": cvar_95,
        "beta": beta,
        "corr_spy": corr_spy,
        "downside_capture": downside_capture,
        "stress_market_down_2": stress_market_down_2,
        "stress_market_down_5": stress_market_down_5,
        "rolling_vol": rolling_vol,
        "rolling_drawdown": rolling_drawdown,
        "top_weight": top_weight,
        "top_3_weight": top_3_weight,
        "effective_positions": effective_positions,
        "survivability_score": survivability_score,
        "survivability_label": survivability_label,
        "exposure_df": exposure_df,
    }

@st.cache_data(show_spinner=False, ttl=300)
def generate_monte_carlo_desk_brief(*args, **kwargs):
    return (
        "[Simulation Read]\n"
        "Monte Carlo engine active.\n\n"
        "[Risk Read]\n"
        "Portfolio dispersion, volatility clustering, and tail outcomes remain within modeled ranges.\n\n"
        "[Desk Takeaway]\n"
        "Simulation paths support long-horizon capital deployment analysis."
    )
@st.cache_data(show_spinner=False, ttl=300)
def generate_risk_desk_brief(risk_engine, portfolio_type, risk_level, horizon):
    return (
        "[Risk Desk Read]\n"
        "Portfolio risk engine active.\n\n"
        "[Stress Conditions]\n"
        "Current allocation remains sensitive to volatility expansion, liquidity compression, and correlation clustering.\n\n"
        "[Desk Directive]\n"
        "Monitor downside capture, concentration risk, and regime transitions closely."
    )


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

def image_to_base64(path):
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"


# -----------------------------
# Disclaimers
# -----------------------------
DISCLAIMER_SMALL = """
<div class="footer-note">
    For educational purposes only. Not investment advice.
</div>
"""

DISCLAIMER_FULL = """
<div style="margin-top:16px; text-align:center; color:rgba(231,238,249,0.55); font-size:0.8rem;">
    This tool is for educational and informational purposes only and does not constitute
    investment advice. Outputs are generated from models and data and may be inaccurate.
    Past performance is not indicative of future results.
</div>
"""

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
        if rate_limit_openai():
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
        )
        else:
            return "AI insight temporarily limited. Please try again in a few minutes."
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
        if rate_limit_openai():
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
            )

            text = (response.output_text or "").strip()

            return text if text else "AI trader insight unavailable right now."

        else:
            return "AI insight temporarily limited. Please try again in a few minutes."

    except Exception:
        return "AI trader insight unavailable right now."

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
active_ticker = st.session_state.active_ticker


if active_ticker:
    header_left, header_right = st.columns([0.38, 0.62], gap="large")

    with header_left:
        st.markdown("<div style='margin-top:-4px;'>", unsafe_allow_html=True)
        st.image("assets/logo.png", width=230)
        st.markdown("</div>", unsafe_allow_html=True)

    with header_right:
        render_market_command_box()

mode = st.radio(
    "",
    ["Stock Lens", "Portfolio Lab", "Allocation Engine"],
    horizontal=True,
    key="mode_toggle",
)

active_ticker = st.session_state.active_ticker

is_landing = mode == "Stock Lens" and not active_ticker



if is_landing:
    st.markdown(
        """
        <style>
        div[data-testid="stRadio"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Landing Page
# -----------------------------
if mode == "Stock Lens" and not active_ticker:
    logo_src = image_to_base64("assets/logo.png")

    landing_html = (
        f'<div style="min-height:820px; margin-top:10px; padding:0; position:relative; overflow:hidden; '
        f'border-radius:0; background:#020713;">'

            f'<div style="position:absolute; inset:0; opacity:0.32; '
            f'background:radial-gradient(900px 520px at 50% 34%, rgba(58,141,255,0.22), transparent 65%), '
            f'radial-gradient(650px 420px at 18% 52%, rgba(46,229,157,0.08), transparent 62%), '
            f'linear-gradient(180deg, rgba(3,10,24,0.98), rgba(1,4,12,1));"></div>'

            f'<div style="position:absolute; inset:0; opacity:0.15; background-image:'
            f'linear-gradient(rgba(58,141,255,0.18) 1px, transparent 1px),'
            f'linear-gradient(90deg, rgba(58,141,255,0.18) 1px, transparent 1px); '
            f'background-size:56px 56px;"></div>'

            f'<div style="position:absolute; left:-40px; bottom:170px; width:38%; height:360px; opacity:0.18; '
            f'background:linear-gradient(110deg, transparent 0%, rgba(58,141,255,0.22) 50%, transparent 100%); '
            f'clip-path:polygon(0 72%, 10% 58%, 18% 66%, 28% 43%, 38% 51%, 48% 30%, 58% 42%, 72% 18%, 100% 10%, 100% 100%, 0 100%);"></div>'

            f'<div style="position:absolute; right:-40px; bottom:150px; width:42%; height:420px; opacity:0.20; '
            f'background:linear-gradient(105deg, transparent 0%, rgba(58,141,255,0.25) 55%, transparent 100%); '
            f'clip-path:polygon(0 80%, 8% 70%, 18% 74%, 28% 52%, 38% 58%, 48% 34%, 60% 39%, 72% 18%, 84% 22%, 100% 0, 100% 100%, 0 100%);"></div>'

            f'<div style="position:absolute; left:0; right:0; top:0; height:76px; border-bottom:1px solid rgba(255,255,255,0.07); '
            f'background:rgba(2,7,19,0.44); backdrop-filter:blur(10px);"></div>'

            f'<div style="position:relative; z-index:3; height:76px; display:flex; align-items:center; justify-content:space-between; padding:0 52px;">'
                f'<img src="{logo_src}" style="width:154px;">'
                f'<div style="display:flex; gap:72px; color:rgba(231,238,249,0.82); font-size:0.86rem; letter-spacing:0.15em; font-weight:700;">'
                    f'<div>STOCK LENS</div>'
                    f'<div>PORTFOLIO LAB</div>'
                    f'<div>ALLOCATION ENGINE</div>'
                f'</div>'
                f'<div style="color:#39A8FF; font-size:0.80rem; letter-spacing:0.08em; font-weight:900;">AI-POWERED MARKET INTELLIGENCE</div>'
            f'</div>'

            f'<div style="position:absolute; inset:0; pointer-events:none; opacity:0.18; z-index:1;">'

                f'<div style="position:absolute; left:3%; top:22%; display:flex; gap:22px; align-items:flex-end;">'
                    f'<div style="position:relative; height:180px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:180px; background:rgba(90,140,255,0.42);"></div>'
                        f'<div style="position:absolute; left:0; top:42px; width:18px; height:76px; background:rgba(90,140,255,0.55); border-radius:3px; box-shadow:0 0 12px rgba(90,140,255,0.32);"></div>'
                    f'</div>'
                    f'<div style="position:relative; height:120px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:120px; background:rgba(90,140,255,0.36);"></div>'
                        f'<div style="position:absolute; left:0; top:30px; width:18px; height:46px; background:rgba(90,140,255,0.48); border-radius:3px; box-shadow:0 0 10px rgba(90,140,255,0.28);"></div>'
                    f'</div>'
                    f'<div style="position:relative; height:210px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:210px; background:rgba(90,140,255,0.46);"></div>'
                        f'<div style="position:absolute; left:0; top:56px; width:18px; height:88px; background:rgba(90,140,255,0.62); border-radius:3px; box-shadow:0 0 14px rgba(90,140,255,0.34);"></div>'
                    f'</div>'
                    f'<div style="position:relative; height:150px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:150px; background:rgba(90,140,255,0.34);"></div>'
                        f'<div style="position:absolute; left:0; top:38px; width:18px; height:58px; background:rgba(90,140,255,0.44); border-radius:3px; box-shadow:0 0 10px rgba(90,140,255,0.24);"></div>'
                    f'</div>'
                    f'<div style="position:relative; height:260px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:260px; background:rgba(90,140,255,0.52);"></div>'
                        f'<div style="position:absolute; left:0; top:74px; width:18px; height:102px; background:rgba(90,140,255,0.70); border-radius:3px; box-shadow:0 0 16px rgba(90,140,255,0.40);"></div>'
                    f'</div>'
                f'</div>'

                f'<div style="position:absolute; right:3%; top:18%; display:flex; gap:22px; align-items:flex-end;">'
                    f'<div style="position:relative; height:240px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:240px; background:rgba(90,140,255,0.46);"></div>'
                        f'<div style="position:absolute; left:0; top:66px; width:18px; height:92px; background:rgba(90,140,255,0.62); border-radius:3px; box-shadow:0 0 14px rgba(90,140,255,0.34);"></div>'
                    f'</div>'
                    f'<div style="position:relative; height:160px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:160px; background:rgba(90,140,255,0.34);"></div>'
                        f'<div style="position:absolute; left:0; top:44px; width:18px; height:60px; background:rgba(90,140,255,0.44); border-radius:3px; box-shadow:0 0 10px rgba(90,140,255,0.24);"></div>'
                    f'</div>'
                    f'<div style="position:relative; height:300px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:300px; background:rgba(90,140,255,0.58);"></div>'
                        f'<div style="position:absolute; left:0; top:88px; width:18px; height:116px; background:rgba(90,140,255,0.78); border-radius:3px; box-shadow:0 0 18px rgba(90,140,255,0.44);"></div>'
                    f'</div>'
                    f'<div style="position:relative; height:210px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:210px; background:rgba(90,140,255,0.42);"></div>'
                        f'<div style="position:absolute; left:0; top:60px; width:18px; height:78px; background:rgba(90,140,255,0.54); border-radius:3px; box-shadow:0 0 12px rgba(90,140,255,0.30);"></div>'
                    f'</div>'
                    f'<div style="position:relative; height:340px; width:18px;">'
                        f'<div style="position:absolute; left:8px; top:0; width:2px; height:340px; background:rgba(90,140,255,0.64);"></div>'
                        f'<div style="position:absolute; left:0; top:102px; width:18px; height:128px; background:rgba(90,140,255,0.86); border-radius:3px; box-shadow:0 0 20px rgba(90,140,255,0.48);"></div>'
                    f'</div>'
                f'</div>'

            f'</div>'

            f'<div style="position:relative; z-index:3; text-align:center; padding-top:165px;">'
                f'<img src="{logo_src}" style="width:520px; max-width:78%; margin-bottom:24px; filter:drop-shadow(0 0 24px rgba(58,141,255,0.35));">'
                f'<div style="font-size:2.35rem; line-height:1.2; font-weight:500; letter-spacing:-0.035em; color:#F5F7FB;">'
                    f'Institutional-grade market <span style="color:#39A8FF;">intelligence.</span>'
                f'</div>'
                f'<div style="margin:22px auto 0 auto; max-width:650px; color:rgba(231,238,249,0.64); font-size:1.16rem; line-height:1.55;">'
                    f'Real-time signals, AI-driven insights, and advanced analytics<br>for any stock or crypto.'
                f'</div>'

                f'<div style="height:94px;"></div>'

                f'<div style="position:relative; z-index:3; display:grid; grid-template-columns:repeat(5,1fr); gap:0; '
                f'margin:112px 58px 0 58px; padding-top:22px;">'

                    f'<div style="text-align:center; border-right:1px solid rgba(255,255,255,0.08); padding:0 22px;">'
                        f'<div style="margin-bottom:28px; display:flex; justify-content:center; align-items:center;">'
                            f'<svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#3A98FF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 10px rgba(58,152,255,0.35));">'
                                f'<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>'
                            f'</svg>'
                        f'</div>'
                        f'<div style="margin-top:16px; color:white; font-weight:900;">REAL-TIME DATA</div>'
                        f'<div style="margin-top:12px; color:rgba(231,238,249,0.55); line-height:1.45;">Live market feeds<br>and price updates</div>'
                    f'</div>'

                    f'<div style="text-align:center; border-right:1px solid rgba(255,255,255,0.08); padding:0 22px;">'
                        f'<div style="margin-bottom:28px; display:flex; justify-content:center; align-items:center;">'
                            f'<svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#3A98FF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 10px rgba(58,152,255,0.35));">'
                                f'<path d="M9.5 2.5C7 2.5 5 4.5 5 7c0 1 .3 1.9.9 2.6C4.1 10.2 3 12 3 14c0 3 2.2 5 5 5h1"/>'
                                f'<path d="M14.5 2.5C17 2.5 19 4.5 19 7c0 1-.3 1.9-.9 2.6C19.9 10.2 21 12 21 14c0 3-2.2 5-5 5h-1"/>'
                                f'<path d="M9 8h.01"/><path d="M15 8h.01"/><path d="M8 13h8"/><path d="M12 8v10"/>'
                            f'</svg>'
                        f'</div>'
                        f'<div style="margin-top:16px; color:white; font-weight:900;">AI SIGNALS</div>'
                        f'<div style="margin-top:12px; color:rgba(231,238,249,0.55); line-height:1.45;">Model-driven insight<br>and signal context</div>'
                    f'</div>'

                    f'<div style="text-align:center; border-right:1px solid rgba(255,255,255,0.08); padding:0 22px;">'
                        f'<div style="margin-bottom:28px; display:flex; justify-content:center; align-items:center;">'
                            f'<svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#3A98FF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 10px rgba(58,152,255,0.35));">'
                                f'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
                                f'<path d="M9 12l2 2 4-4"/>'
                            f'</svg>'
                        f'</div>'
                        f'<div style="margin-top:16px; color:white; font-weight:900;">RISK ANALYSIS</div>'
                        f'<div style="margin-top:12px; color:rgba(231,238,249,0.55); line-height:1.45;">Volatility tracking<br>and risk scoring</div>'
                    f'</div>'

                    f'<div style="text-align:center; border-right:1px solid rgba(255,255,255,0.08); padding:0 22px;">'
                        f'<div style="margin-bottom:28px; display:flex; justify-content:center; align-items:center;">'
                            f'<svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#3A98FF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 10px rgba(58,152,255,0.35));">'
                                f'<path d="M21.21 15.89A10 10 0 1 1 12 2v10z"/>'
                                f'<path d="M22 12A10 10 0 0 0 12 2v10z"/>'
                            f'</svg>'
                        f'</div>'
                        f'<div style="margin-top:16px; color:white; font-weight:900;">PORTFOLIO LAB</div>'
                        f'<div style="margin-top:12px; color:rgba(231,238,249,0.55); line-height:1.45;">Backtest portfolios<br>against benchmarks</div>'
                    f'</div>'

                    f'<div style="text-align:center; padding:0 22px;">'
                        f'<div style="margin-bottom:28px; display:flex; justify-content:center; align-items:center;">'
                            f'<svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#3A98FF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 10px rgba(58,152,255,0.35));">'
                                f'<rect x="3" y="3" width="7" height="7" rx="1"/>'
                                f'<rect x="14" y="3" width="7" height="7" rx="1"/>'
                                f'<rect x="3" y="14" width="7" height="7" rx="1"/>'
                                f'<rect x="14" y="14" width="7" height="7" rx="1"/>'
                            f'</svg>'
                        f'</div>'
                        f'<div style="margin-top:16px; color:white; font-weight:900;">ALLOCATION ENGINE</div>'
                        f'<div style="margin-top:12px; color:rgba(231,238,249,0.55); line-height:1.45;">Smart allocation<br>across asset sleeves</div>'
                    f'</div>'

                f'</div>'

                f'<div style="position:relative; z-index:3; margin-top:62px; text-align:center; color:rgba(231,238,249,0.38); font-size:0.86rem;">'
                    f'© 2026 AInvest. For educational purposes only. Not investment advice.'
                f'</div>'

            f'</div>'

        f'</div>'
    )

    st.markdown(landing_html, unsafe_allow_html=True)

    st.markdown(
    """
    <style>
    div[data-testid="stTextInput"]:has(input[aria-label="Landing Ticker Input"]) {
        width: 650px !important;
        max-width: 88% !important;
        margin: -455px auto 360px auto !important;
        position: relative !important;
        z-index: 999 !important;
    }

    div[data-testid="stTextInput"]:has(input[aria-label="Landing Ticker Input"]) > div {
        min-height: 62px !important;
    }

    div[data-testid="stTextInput"]:has(input[aria-label="Landing Ticker Input"]) div[data-baseweb="input"] {
        height: 62px !important;
        min-height: 62px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(115,207,255,0.72) !important;
        background: rgba(5,14,32,0.78) !important;
        box-shadow: 0 0 28px rgba(58,141,255,0.20) !important;
    }

    div[data-testid="stTextInput"]:has(input[aria-label="Landing Ticker Input"]) input {
        height: 62px !important;
        min-height: 62px !important;
        color: #E7EEF9 !important;
        font-size: 1.05rem !important;
        padding-left: 52px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

    landing_ticker = st.text_input(
        "Landing Ticker Input",
            placeholder="›   Enter ticker (AAPL, NVDA, BTC-USD)",
            label_visibility="collapsed",
            key="landing_ticker_input",
    ).strip().upper()

    if landing_ticker:
        st.session_state.active_ticker = landing_ticker
        st.rerun()

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:-415px;
            margin-bottom:385px;
            color:#39A8FF;
            font-size:0.90rem;
            letter-spacing:0.04em;
            font-weight:500;
        ">
            Press Enter to run analysis
        </div>
        """,
        unsafe_allow_html=True,
    )
    
if mode == "Stock Lens" and active_ticker:
    input_col, button_col = st.columns([4, 1], gap="medium")

    with input_col:
        typed_ticker = st.text_input(
            "Ticker Input",
            value=active_ticker,
            placeholder="Enter ticker",
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
        headlines = fetch_alpaca_headlines(active_ticker)

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

        confidence = snapshot.get("confidence", 50)
        risk = snapshot.get("risk", "Medium")
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
                f'{(ai_text or "No AI insight available yet.").replace(chr(10), "<br>")}'
                f'</div>'

                f'</div>'
            )
            st.markdown(insight_html, unsafe_allow_html=True)

        with bottom_right:
            headline_rows = ""

            if headlines:
                for h in headlines[:4]:
                    if isinstance(h, dict):
                        title = h.get("title", "Headline")
                        url = h.get("url") or h.get("link")
                    else:
                        title = str(h)
                        url = None

                    if url:
                        headline_rows += (
                            f'<a href="{url}" target="_blank" style="text-decoration:none;">'
                                f'<div class="headline-item" style="'
                                f'padding:11px 0; '
                                f'border-bottom:1px solid rgba(255,255,255,0.08); '
                                f'color:#E7EEF9; '
                                f'font-size:0.86rem; '
                                f'line-height:1.45; '
                                f'font-weight:750;">'
                                    f'{title}'
                                f'</div>'
                            f'</a>'
                        )
                    else:
                        headline_rows += (
                            f'<div class="headline-item" style="'
                            f'padding:11px 0; '
                            f'border-bottom:1px solid rgba(255,255,255,0.08); '
                            f'color:#E7EEF9; '
                            f'font-size:0.86rem; '
                            f'line-height:1.45; '
                            f'font-weight:750;">'
                                f'{title}'
                            f'</div>'
                        )
            else:
                headline_rows = (
                    f'<div style="color:rgba(231,238,249,0.62); font-size:0.86rem;">'
                    f'No recent headlines available.'
                    f'</div>'
                )

            news_html = (
                f'<div class="bottom-card" style="padding:18px;">'
                    f'<div class="card-heading" style="margin-bottom:8px;">'
                        f'<div class="card-title">Latest Headlines</div>'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.50); margin-top:3px;">'
                            f'Recent ticker-specific market news'
                        f'</div>'
                    f'</div>'
                    f'<div class="card-body">'
                        f'{headline_rows}'
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
        st.markdown(DISCLAIMER_SMALL, unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=900)
def calculate_allocation_risk_contribution(allocation, assets, timeframe):
    period_map = {
        "1Y": "1y",
        "3Y": "3y",
        "5Y": "5y",
        "10Y": "10y",
    }

    period = period_map.get(timeframe, "5y")

    bucket_vols = {}

    for bucket, asset_text in assets.items():
        tickers = [
            t.strip()
            for t in asset_text.replace("/", ",").replace("+", ",").split(",")
            if t.strip() and t.strip().upper() not in ["CASH", "SHY"]
        ]

        if not tickers:
            bucket_vols[bucket] = 2.0
            continue

        try:
            prices = yf.download(
                tickers,
                period=period,
                auto_adjust=True,
                progress=False
            )["Close"]

            if isinstance(prices, pd.Series):
                prices = prices.to_frame()

            returns = prices.dropna(axis=1, how="all").ffill().pct_change().dropna()

            if returns.empty:
                bucket_vols[bucket] = 10.0
            else:
                bucket_returns = returns.mean(axis=1)
                bucket_vols[bucket] = float(bucket_returns.std() * np.sqrt(252) * 100)

        except Exception:
            bucket_vols[bucket] = 10.0

    raw_risk = {
        bucket: allocation[bucket] * bucket_vols[bucket]
        for bucket in allocation
    }

    total_risk = sum(raw_risk.values())

    if total_risk == 0:
        return {}

    return {
        bucket: (value / total_risk) * 100
        for bucket, value in raw_risk.items()
    }

@st.cache_data(show_spinner=False, ttl=300)
def build_recommended_buys(allocation, assets, portfolio_size):
    pools = {
        "Core Beta": ["SPY", "VTI"],
        "Growth Tilt": ["QQQ", "NVDA", "MSFT", "AMZN", "SMH"],
        "Defensive Hedge": ["TLT", "GLD"],
        "Alpha Sleeve": ["MSTR", "TSLA"],
        "Liquidity": ["SHY"],
    }

    all_tickers = sorted({t for tickers in pools.values() for t in tickers})

    prices = yf.download(
        all_tickers,
        period="5d",
        auto_adjust=True,
        progress=False
    )["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    latest_prices = prices.ffill().iloc[-1]

    results = []

    for bucket, weight in allocation.items():
        tickers = pools.get(bucket, [])
        if not tickers:
            continue

        bucket_dollars = portfolio_size * (weight / 100)
        dollars_per_stock = bucket_dollars / len(tickers)

        for ticker in tickers:
            if ticker not in latest_prices.index:
                continue

            price = float(latest_prices[ticker])

            if price <= 0:
                continue

            shares = dollars_per_stock / price

            results.append({
                "ticker": ticker,
                "bucket": bucket,
                "price": price,
                "shares": shares,
                "dollars": dollars_per_stock,
            })

    return results

@st.cache_data(show_spinner=False, ttl=900)
def calculate_allocation_live_performance(recommendations, timeframe):
    period_map = {
        "1Y": "1y",
        "3Y": "3y",
        "5Y": "5y",
        "10Y": "10y",
    }

    period = period_map.get(timeframe, "5y")

    tickers = [p["ticker"] for p in recommendations if p["ticker"] != "CASH"]

    benchmark_tickers = [
        "SPY",
        "QQQ",
        "SMH",
        "NVDA",
        "MSFT",
        "AAPL",
        "AMZN",
        "GOOGL",
        "TLT",
    ]

    tickers = sorted(list(set(tickers + benchmark_tickers)))
    prices = yf.download(
        tickers,
        period=period,
        auto_adjust=True,
        progress=False
    )["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    prices = prices.dropna(axis=1, how="all").ffill().dropna()

    valid_picks = [p for p in recommendations if p["ticker"] in prices.columns]

    if not valid_picks or "SPY" not in prices.columns:
        return None

    returns = prices.pct_change().dropna()

    total_dollars = sum(p["dollars"] for p in valid_picks)

    weights = {
        p["ticker"]: p["dollars"] / total_dollars
        for p in valid_picks
    }

    portfolio_returns = sum(
        returns[ticker] * weight
        for ticker, weight in weights.items()
        if ticker in returns.columns
    )

    benchmark_returns = {}

    # SPY
    if "SPY" in returns.columns:
        benchmark_returns["SPY"] = returns["SPY"]

    # Growth Strategy
    if "QQQ" in returns.columns and "SMH" in returns.columns:
        benchmark_returns["Growth Strategy"] = returns[["QQQ", "SMH"]].dot([0.7, 0.3])

    # Concentrated Alpha
    alpha_names = [t for t in ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"] if t in returns.columns]
    if alpha_names:
        benchmark_returns["Concentrated Alpha"] = returns[alpha_names].mean(axis=1)

    # Defensive Allocation
    if "SPY" in returns.columns and "TLT" in returns.columns:
        benchmark_returns["Defensive Allocation"] = returns[["SPY", "TLT"]].dot([0.6, 0.4])

    spy_returns = returns["SPY"]

    annual_return = ((1 + portfolio_returns).prod() ** (252 / len(portfolio_returns)) - 1) * 100
    volatility = portfolio_returns.std() * np.sqrt(252) * 100

    cumulative = (1 + portfolio_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown_series = (cumulative / running_max - 1) * 100
    max_drawdown = drawdown_series.min()

    sharpe = annual_return / volatility if volatility != 0 else 0

    spy_annual_return = ((1 + spy_returns).prod() ** (252 / len(spy_returns)) - 1) * 100
    vs_spy = annual_return - spy_annual_return

    chart_df = pd.DataFrame({
    "Allocation Engine": portfolio_returns,
    **benchmark_returns
    }).dropna()

    growth = (1 + chart_df).cumprod() * 100

    return {
        "annual_return": annual_return,
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "spy_annual_return": spy_annual_return,
        "vs_spy": vs_spy,
        "growth": growth,
        "weights": weights,
    }

@st.cache_data(show_spinner=False, ttl=300)
def generate_allocation_brief(
    portfolio_type,
    risk_level,
    expected_return,
    volatility,
    drawdown,
    sharpe,
    vs_spy,
    best_strategy,
    closest,
    gap_driver,
    outperformance,
    timeframe
):
    if not api_key or client is None:
        return "AI allocation brief unavailable because OPENAI_API_KEY is not set."

    prompt = f"""
You are a senior portfolio manager designing an institutional allocation.

This is YOUR portfolio construction.

Write like you built it.

Tone:
- internal desk note (not client-facing)
- sharp and compressed
- avoid full sentences when possible
- prefer fragments over explanations
- no polished or academic language
- no “designed to”, “aims to”, “intended to”
- write like a PM thinking, not presenting

Structure EXACTLY like this:

[Positioning]
1 short paragraph explaining how capital is intentionally allocated and why.

[Exposure]
- 2–3 bullets
- where capital is concentrated
- what factors drive performance

[Risk]
- 2 bullets
- where this allocation fails

[Adjustment]
- 1–2 bullets
- what YOU would change if conditions shift

[Takeaway]
ONE line, blunt (max 10 words)

Data:
Portfolio type: {portfolio_type}
Risk level: {risk_level}
Timeframe: {timeframe}
Expected return: {expected_return}
Volatility: {volatility}
Max drawdown: {drawdown}
Sharpe: {sharpe}
Vs SPY: {vs_spy}

Benchmark context:
Top performer: {best_strategy}
Closest match: {closest}
Gap driver: {gap_driver}
Performance gap: {outperformance:.1f} pts
"""

    try:
        if rate_limit_openai():

            response = client.responses.create(

                model="gpt-4.1-mini",

                input=prompt,

            )

            text = (response.output_text or "").strip()

            return text if text else "AI trader insight unavailable right now."

        else:

            return "AI insight temporarily limited. Please try again in a few minutes."
    except Exception:
        return "AI allocation brief unavailable right now."
    
@st.cache_data(show_spinner=False, ttl=900)
def calculate_allocation_correlation_matrix(recommendations, timeframe):
    period_map = {
        "1Y": "1y",
        "3Y": "3y",
        "5Y": "5y",
        "10Y": "10y",
    }

    period = period_map.get(timeframe, "5y")

    tickers = [p["ticker"] for p in recommendations if p["ticker"] != "CASH"]

    if len(tickers) < 2:
        return None

    prices = yf.download(
        tickers,
        period=period,
        auto_adjust=True,
        progress=False
    )["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    prices = prices.dropna(axis=1, how="all").ffill().dropna()

    if prices.shape[1] < 2:
        return None

    returns = prices.pct_change().dropna()

    if returns.empty:
        return None

    corr = returns.corr()

    return corr

@st.cache_data(show_spinner=False, ttl=900)
def calculate_market_regime():
    tickers = ["SPY", "QQQ", "TLT", "GLD", "UUP", "^VIX"]

    try:
        prices = yf.download(
            tickers,
            period="6mo",
            auto_adjust=True,
            progress=False
        )["Close"]

        if isinstance(prices, pd.Series):
            prices = prices.to_frame()

        prices = prices.dropna(axis=1, how="all").ffill().dropna()

        spy_return = (prices["SPY"].iloc[-1] / prices["SPY"].iloc[0] - 1) * 100 if "SPY" in prices else 0
        qqq_return = (prices["QQQ"].iloc[-1] / prices["QQQ"].iloc[0] - 1) * 100 if "QQQ" in prices else 0
        tlt_return = (prices["TLT"].iloc[-1] / prices["TLT"].iloc[0] - 1) * 100 if "TLT" in prices else 0
        gld_return = (prices["GLD"].iloc[-1] / prices["GLD"].iloc[0] - 1) * 100 if "GLD" in prices else 0
        vix_level = float(prices["^VIX"].iloc[-1]) if "^VIX" in prices else 18

        risk_on_score = 50
        risk_on_score += 20 if spy_return > 5 else -10 if spy_return < -5 else 0
        risk_on_score += 15 if qqq_return > spy_return else -8
        risk_on_score += 10 if vix_level < 18 else -20 if vix_level > 25 else 0
        risk_on_score += 5 if tlt_return < spy_return else -5

        risk_on_score = max(0, min(100, risk_on_score))

        if risk_on_score >= 70:
            regime = "Risk-On Expansion"
            color = "#2EE59D"
        elif risk_on_score >= 55:
            regime = "Late-Cycle Growth"
            color = "#FFB020"
        elif risk_on_score >= 40:
            regime = "Mixed / Transition"
            color = "#73CFFF"
        else:
            regime = "Risk-Off Stress"
            color = "#FF4D6D"

        recession_prob = max(3, min(45, 100 - risk_on_score))
        risk_off_prob = max(5, min(35, 75 - risk_on_score))
        late_cycle_prob = max(10, min(35, 100 - abs(risk_on_score - 60)))
        risk_on_prob = max(5, min(85, risk_on_score))

        total = risk_on_prob + late_cycle_prob + risk_off_prob + recession_prob

        probabilities = {
            "Risk-On": risk_on_prob / total * 100,
            "Late Cycle": late_cycle_prob / total * 100,
            "Risk-Off": risk_off_prob / total * 100,
            "Recession": recession_prob / total * 100,
        }

        return {
            "regime": regime,
            "color": color,
            "score": risk_on_score,
            "vix": vix_level,
            "spy_return": spy_return,
            "qqq_return": qqq_return,
            "tlt_return": tlt_return,
            "gld_return": gld_return,
            "probabilities": probabilities,
        }

    except Exception:
        return {
            "regime": "Regime Unavailable",
            "color": "#94A3B8",
            "score": 0,
            "vix": 0,
            "spy_return": 0,
            "qqq_return": 0,
            "tlt_return": 0,
            "gld_return": 0,
            "probabilities": {
                "Risk-On": 0,
                "Late Cycle": 0,
                "Risk-Off": 0,
                "Recession": 0,
            },
        }
    
  # =========================================================
# 🟢 MARKET REGIME AI PROMPT ENGINE
# Institutional macro / trading desk interpretation system
# =========================================================  
@st.cache_data(show_spinner=False, ttl=300)
def generate_market_regime_brief(market_regime, portfolio_type, risk_level, allocation, assets):
    if not api_key or client is None:
        return "AI regime interpretation unavailable because OPENAI_API_KEY is not set."

    allocation_text = ", ".join([f"{k}: {v}%" for k, v in allocation.items()])
    assets_text = " | ".join([f"{k}: {v}" for k, v in assets.items()])

    prompt = f"""
You are a senior macro/derivatives strategist writing for an internal institutional trading desk.

Audience:
- Citadel-style trading desk
- PMs, risk managers, analysts
- NOT retail investors
- assume the reader understands beta, vol, duration, risk-on/risk-off, factor leadership, and drawdown risk

Voice:
- internal desk note
- sharp
- compressed
- direct
- slightly blunt
- no client-facing language
- no education tone
- no disclaimers
- no hype
- avoid full sentences when fragments are stronger

Current tape:
Regime: {market_regime["regime"]}
Regime score: {market_regime["score"]:.0f}/100
VIX: {market_regime["vix"]:.1f}
SPY 6M: {market_regime["spy_return"]:+.1f}%
QQQ 6M: {market_regime["qqq_return"]:+.1f}%
TLT 6M: {market_regime["tlt_return"]:+.1f}%
GLD 6M: {market_regime["gld_return"]:+.1f}%

Regime probabilities:
Risk-On: {market_regime["probabilities"]["Risk-On"]:.0f}%
Late Cycle: {market_regime["probabilities"]["Late Cycle"]:.0f}%
Risk-Off: {market_regime["probabilities"]["Risk-Off"]:.0f}%
Recession: {market_regime["probabilities"]["Recession"]:.0f}%

Current book:
Portfolio type: {portfolio_type}
Risk level: {risk_level}
Allocation: {allocation_text}
Assets: {assets_text}

Write EXACTLY in this structure:

[Desk Read]
One tight paragraph. Explain what the tape is doing and what regime the book is sitting in.

[Signal Stack]
- 3 bullets max
- focus on what matters: equity trend, growth leadership, vol pressure, duration/GLD behavior

[Book Impact]
- 2 bullets max
- explain what this regime does to the current allocation

[Transition Triggers]
- 2 bullets max
- what would force the desk to change posture

[Action Bias]
One blunt line. Max 12 words.

Rules:
- no phrases like "investors should"
- no "this suggests"
- no "it may indicate"
- no public-facing explanation
- no generic advice
- do not define terms
- do not mention AI
- do not mention educational use
- write like internal PM/risk desk language
- keep total response under 170 words
- prioritize compressed institutional language
- short bullets preferred over paragraphs
- avoid long explanations
- no paragraph longer than 2 sentences
- sound like internal PM/risk desk communication
- concise > polished
- density of insight matters more than readability
"""

    try:
        if rate_limit_openai():
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
            )

            text = (response.output_text or "").strip()

            return text if text else "AI trader insight unavailable right now."

        else:
            return "AI insight temporarily limited. Please try again in a few minutes."

    except Exception:
        return "AI trader insight unavailable right now."


if mode == "Allocation Engine":
    # -----------------------------
    # Wide terminal CSS override
    # -----------------------------
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1820px !important;
            padding-left: 1.1rem !important;
            padding-right: 1.1rem !important;
            padding-top: 0.8rem !important;
        }

        [data-testid="stAppViewContainer"] .main {
            max-width: none !important;
        }

        .terminal-shell {
            width: 100%;
        }

        .terminal-nav-title {
            font-size: 1.45rem;
            font-weight: 950;
            color: #E7EEF9;
            letter-spacing: -0.03em;
        }

        .terminal-nav-subtitle {
            color: rgba(231,238,249,0.58);
            font-size: 0.78rem;
            margin-bottom: 12px;
        }

        .engine-section-title {
            font-size: 1.35rem;
            font-weight: 950;
            color: #E7EEF9;
            letter-spacing: -0.03em;
            margin: 10px 0 8px 0;
        }

        .mini-label {
            color: rgba(231,238,249,0.58);
            font-size: 0.72rem;
            font-weight: 800;
        }

        .mini-value {
            color: #E7EEF9;
            font-size: 1.05rem;
            font-weight: 950;
            margin-top: 3px;
        }

        .engine-card-title {
            color: #E7EEF9;
            font-size: 0.98rem;
            font-weight: 950;
            margin-bottom: 8px;
        }

        .engine-card-body {
            color: rgba(231,238,249,0.72);
            font-size: 0.82rem;
            line-height: 1.45;
        }

        .stSlider label, .stNumberInput label, label {
            color: #E7EEF9 !important;
            font-weight: 800 !important;
        }

        .stNumberInput input {
            color: #FFFFFF !important;
            font-weight: 800 !important;
            background-color: #091733 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------
    # Session state
    # -----------------------------
    if "allocation_engine_view" not in st.session_state:
        st.session_state.allocation_engine_view = "Command Center"
    if "allocation_mandate" not in st.session_state:
        st.session_state.allocation_mandate = "Growth"
    if "allocation_risk" not in st.session_state:
        st.session_state.allocation_risk = "Medium"
    if "allocation_horizon" not in st.session_state:
        st.session_state.allocation_horizon = "5Y"
    if "allocation_portfolio_size" not in st.session_state:
        st.session_state.allocation_portfolio_size = 100000
    if "mc_auto_simulations" not in st.session_state:
        st.session_state.mc_auto_simulations = 500

    mandate = st.session_state.allocation_mandate
    risk = st.session_state.allocation_risk
    portfolio_size = st.session_state.allocation_portfolio_size

    # -----------------------------
    # Allocation model
    # -----------------------------
    if mandate == "Defensive" or risk == "Low":
        allocation = {
            "Core Beta": 40,
            "Defensive Hedge": 35,
            "Growth Tilt": 15,
            "Alpha Sleeve": 5,
            "Liquidity": 5,
        }
        assets = {
            "Core Beta": "SPY",
            "Defensive Hedge": "TLT, GLD",
            "Growth Tilt": "QQQ",
            "Alpha Sleeve": "Low beta equities",
            "Liquidity": "Cash / SHY",
        }
        portfolio_type = "Defensive Multi-Asset Allocation"
        risk_level = "Low-Medium"

    elif mandate == "Opportunistic" or risk == "High":
        allocation = {
            "Core Beta": 35,
            "Growth Tilt": 35,
            "Alpha Sleeve": 20,
            "Defensive Hedge": 5,
            "Liquidity": 5,
        }
        assets = {
            "Core Beta": "SPY",
            "Growth Tilt": "QQQ, SMH",
            "Alpha Sleeve": "MSTR, NVDA",
            "Defensive Hedge": "GLD",
            "Liquidity": "Cash / SHY",
        }
        portfolio_type = "Aggressive Growth / Alpha Allocation"
        risk_level = "High"

    else:
        allocation = {
            "Core Beta": 45,
            "Growth Tilt": 25,
            "Defensive Hedge": 15,
            "Alpha Sleeve": 10,
            "Liquidity": 5,
        }
        assets = {
            "Core Beta": "SPY",
            "Growth Tilt": "QQQ, SMH",
            "Defensive Hedge": "TLT, GLD",
            "Alpha Sleeve": "MSTR / selective tech",
            "Liquidity": "Cash / SHY",
        }
        portfolio_type = "Balanced Growth Allocation"
        risk_level = "Medium"

    bucket_colors = {
        "Core Beta": "#3A8DFF",
        "Growth Tilt": "#2EE59D",
        "Defensive Hedge": "#FFB020",
        "Alpha Sleeve": "#9B5CF6",
        "Liquidity": "#94A3B8",
    }

    risk_color = "#FF4D6D" if risk_level == "High" else "#FFB020" if "Medium" in risk_level else "#2EE59D"

    recommendations = build_recommended_buys(allocation, assets, portfolio_size)
    live_perf = calculate_allocation_live_performance(recommendations, st.session_state.allocation_horizon)

    if live_perf:
        expected_return = f"{live_perf['annual_return']:.1f}%"
        volatility = f"{live_perf['volatility']:.1f}%"
        drawdown = f"{live_perf['max_drawdown']:.1f}%"
        sharpe = f"{live_perf['sharpe']:.2f}"
        vs_spy = f"{live_perf['vs_spy']:+.1f}%"
        years = int(st.session_state.allocation_horizon.replace("Y", ""))
        projected_value = portfolio_size * ((1 + live_perf["annual_return"] / 100) ** years)
        projected_gain = projected_value - portfolio_size
        projected_value_text = f"${projected_value:,.0f}"
        projected_gain_text = f"${projected_gain:,.0f}"
        growth = live_perf["growth"]
    else:
        expected_return = "—"
        volatility = "—"
        drawdown = "—"
        sharpe = "—"
        vs_spy = "—"
        projected_value = portfolio_size
        projected_gain = 0
        projected_value_text = "—"
        projected_gain_text = "—"
        growth = None

    best_strategy = "—"
    closest = "—"
    gap_driver = "Benchmark data unavailable."
    outperformance = 0

    if growth is not None and "Allocation Engine" in growth.columns:
        latest = growth.iloc[-1]
        your_value = latest["Allocation Engine"]
        others = latest.drop("Allocation Engine")
        if not others.empty:
            best_strategy = others.idxmax()
            best_value = others.max()
            outperformance = best_value - your_value
            closest = (others - your_value).abs().idxmin()
            if best_strategy == "Concentrated Alpha":
                gap_driver = "High-concentration tech exposure is driving the performance gap."
            elif best_strategy == "Growth Strategy":
                gap_driver = "Growth and semiconductor exposure is driving the performance gap."
            elif best_strategy == "Defensive Allocation":
                gap_driver = "Lower-volatility positioning is reducing drawdowns but capping upside."
            else:
                gap_driver = "Portfolio composition differences are driving the performance gap."

    market_regime = calculate_market_regime()

    # -----------------------------
    # Auto Monte Carlo
    # -----------------------------

    mc = None
    try:
        mc_tickers = [p["ticker"] for p in recommendations if p["ticker"] != "CASH"]
        total_dollars_mc = sum(p["dollars"] for p in recommendations if p["ticker"] != "CASH")
        mc_weights = [
            p["dollars"] / total_dollars_mc
            for p in recommendations
            if p["ticker"] != "CASH"
        ]

        mc = run_monte_carlo(
            tickers=mc_tickers,
            weights=mc_weights,
            initial_value=portfolio_size,
            years=int(st.session_state.allocation_horizon.replace("Y", "")),
            simulations=st.session_state.mc_auto_simulations,
        )
    except Exception:
        mc = None

    # -----------------------------
    # Main terminal layout
    # -----------------------------
    nav_col, terminal_col = st.columns([0.72, 5.9], gap="medium")

    # -----------------------------
    # Left command selector
    # -----------------------------
    with nav_col:
        st.markdown(
            f'<div class="portfolio-card" style="padding:16px 12px; margin-bottom:10px;">'
                f'<div style="display:flex; align-items:center; gap:10px;">'
                    f'<div style="width:34px; height:34px; border-radius:10px; background:linear-gradient(135deg,#3A8DFF,#4B5DFF); '
                    f'display:flex; align-items:center; justify-content:center; font-weight:950; color:white;">A</div>'
                    f'<div>'
                        f'<div style="font-size:1.35rem; font-weight:950; color:#E7EEF9; letter-spacing:-0.04em;">AInvest</div>'
                        f'<div style="color:rgba(231,238,249,0.52); font-size:0.72rem;">Command Terminal</div>'
                    f'</div>'
                f'</div>'
                f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:16px 0;"></div>'
                f'<div style="color:rgba(231,238,249,0.45); font-size:0.68rem; font-weight:900; letter-spacing:0.12em; margin-bottom:8px;">'
                    f'PORTFOLIO SYSTEMS'
                f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                color:rgba(231,238,249,0.45);
                font-size:0.58rem;
                font-weight:900;
                letter-spacing:0.12em;
                margin-top:10px;
                margin-bottom:8px;
            ">
                ANALYTICAL ENGINES
            </div>
            """,
            unsafe_allow_html=True,
        )

        engine_views = [
            "Command Center",
            "Monte Carlo Engine",
            "Risk Engine",
            "Stress Test Engine",
            "Factor Engine",
            "Correlation Engine",
            "Scenario Engine",
            "Market Regime Engine",
        ]

        for view in engine_views:
            active = st.session_state.allocation_engine_view == view

            if st.button(
                view,
                key=f"allocation_engine_{view}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.allocation_engine_view = view
                st.rerun()

        st.markdown(
            """
            <div style="
                color:rgba(231,238,249,0.45);
                font-size:0.58rem;
                font-weight:900;
                letter-spacing:0.12em;
                margin-top:14px;
                margin-bottom:8px;
            ">
                AI LAYER
            </div>
            """,
            unsafe_allow_html=True,
        )

        ai_views = [
            "AI Insights",
            "AI Recommendations",
        ]

        for view in ai_views:
            active = st.session_state.allocation_engine_view == view

            if st.button(
                view,
                key=f"allocation_engine_{view}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.allocation_engine_view = view
                st.rerun()

        st.markdown(
            f'<div class="portfolio-card" style="margin-top:12px; padding:12px;">'
                f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                    f'<div class="mini-label">MARKET REGIME</div>'
                    f'<div style="width:8px; height:8px; border-radius:50%; background:#2EE59D; box-shadow:0 0 10px #2EE59D;"></div>'
                f'</div>'
                f'<div style="color:#2EE59D; font-size:1.05rem; font-weight:950; margin-top:6px;">Risk-On</div>'
                f'<div style="height:46px; margin-top:10px; border-radius:10px; '
                f'background:linear-gradient(135deg, rgba(46,229,157,0.03), rgba(46,229,157,0.18)); '
                f'border-bottom:1px solid rgba(46,229,157,0.35);"></div>'
                f'<div style="display:flex; justify-content:space-between; margin-top:10px; color:rgba(231,238,249,0.45); font-size:0.68rem;">'
                    f'<span>Status</span><span style="color:#2EE59D;">LIVE</span>'
                f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # -----------------------------
    # Terminal screen
    # -----------------------------
    with terminal_col:
        selected_view = st.session_state.allocation_engine_view

        st.markdown(
            f'<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:18px; margin-bottom:12px;">'
                f'<div>'
                    f'<div style="font-size:2rem; font-weight:950; color:#E7EEF9; letter-spacing:-0.04em;">Allocation Engine</div>'
                    f'<div style="color:rgba(231,238,249,0.66); font-size:0.92rem;">AI-powered portfolio construction and analysis</div>'
                f'</div>'
                f'<div style="display:flex; gap:10px; align-items:center;">'
                    f'<div class="portfolio-card" style="padding:8px 12px; min-width:230px; font-size:0.82rem; color:#E7EEF9;">Portfolio: <b>{portfolio_type}</b></div>'
                    f'<div class="portfolio-card" style="padding:8px 12px; font-size:0.82rem; color:#E7EEF9;">Save Portfolio</div>'
                    f'<div class="portfolio-card" style="padding:8px 12px; font-size:0.82rem; color:#E7EEF9;">Export</div>'
                f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div style="display:grid; grid-template-columns:repeat(7, minmax(0, 1fr)); gap:10px; margin-bottom:14px;">'
                f'<div class="metric-tile"><div class="metric-label">Portfolio Value</div><div class="metric-value">${portfolio_size:,.0f}</div></div>'
                f'<div class="metric-tile"><div class="metric-label">Projected Return ({st.session_state.allocation_horizon})</div><div class="metric-value">{expected_return}</div><div style="font-size:0.72rem; color:#2EE59D;">vs SPY {vs_spy}</div></div>'
                f'<div class="metric-tile"><div class="metric-label">Volatility ({st.session_state.allocation_horizon})</div><div class="metric-value">{volatility}</div></div>'
                f'<div class="metric-tile"><div class="metric-label">Max Drawdown ({st.session_state.allocation_horizon})</div><div class="metric-value" style="color:#FF4D6D;">{drawdown}</div></div>'
                f'<div class="metric-tile"><div class="metric-label">Sharpe Ratio</div><div class="metric-value">{sharpe}</div></div>'
                f'<div class="metric-tile"><div class="metric-label">Risk Level</div><div class="metric-value" style="color:{risk_color};">{risk_level}</div><div style="height:6px; border-radius:99px; margin-top:8px; background:linear-gradient(90deg,#2EE59D,#FFB020,#FF4D6D);"></div></div>'
                f'<div class="metric-tile"><div class="metric-label">SPY Outperformance</div><div class="metric-value">{vs_spy}</div><div style="font-size:0.72rem; color:rgba(231,238,249,0.55);">{st.session_state.allocation_horizon} horizon</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

         # -----------------------------
        # Deep-dive pages
        # -----------------------------
        if selected_view == "Monte Carlo Engine":
            st.markdown(
                """
                <style>
                @keyframes mcPulse {
                    0% { opacity:0.72; filter:brightness(0.95); }
                    50% { opacity:1; filter:brightness(1.18); }
                    100% { opacity:0.72; filter:brightness(0.95); }
                }
                .mc-live-bar {
                    animation: mcPulse 2.4s ease-in-out infinite;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # -----------------------------
            # Header
            # -----------------------------
            st.markdown(
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<div>'
                            f'<div style="font-size:1.9rem; font-weight:950; color:#E7EEF9;">'
                                f'Probabilistic Capital Outcomes Engine'
                            f'</div>'
                            f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">'
                                f'Monte Carlo deep dive for {portfolio_type}.'
                            f'</div>'
                        f'</div>'
                        f'<div style="text-align:right;">'
                            f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.52);">SIMULATION MODEL</div>'
                            f'<div style="font-size:1rem; color:#2EE59D; font-weight:900;">LIVE</div>'
                        f'</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # -----------------------------
            # Controls
            # -----------------------------
            control_cols = st.columns([1, 1, 1, 1, 1, 1], gap="medium")

            with control_cols[0]:
                mc_deep_value = st.number_input(
                    "Initial Value",
                    min_value=1000,
                    max_value=10000000,
                    step=1000,
                    value=int(portfolio_size),
                    key="mc_deep_value"
                )

            with control_cols[1]:
                mc_deep_years = st.slider(
                    "Years",
                    1,
                    30,
                    int(st.session_state.allocation_horizon.replace("Y", "")),
                    key="mc_deep_years"
                )

            with control_cols[2]:
                mc_deep_sims = st.slider(
                    "Simulations",
                    500,
                    2000,
                    500,
                    step=500,
                    key="mc_deep_sims"
                )

            with control_cols[3]:
                mc_stress = st.slider(
                    "Volatility Stress",
                    0.5,
                    3.0,
                    1.0,
                    step=0.1,
                    key="mc_stress"
                )

            with control_cols[4]:
                confidence_band = st.selectbox(
                    "Confidence Band",
                    ["90%", "95%", "99%"],
                    index=1,
                    key="mc_confidence_band"
                )

            with control_cols[5]:
                rebalance_mode = st.selectbox(
                    "Rebalancing",
                    ["Quarterly", "Monthly", "No Rebalance", "Vol Target"],
                    index=0,
                    key="mc_rebalance_mode"
                )

            # -----------------------------
            # Run Monte Carlo
            # -----------------------------
            mc_tickers = [p["ticker"] for p in recommendations if p["ticker"] != "CASH"]

            total_dollars_mc = sum(
                p["dollars"] for p in recommendations
                if p["ticker"] != "CASH"
            )

            mc_weights = [
                p["dollars"] / total_dollars_mc
                for p in recommendations
                if p["ticker"] != "CASH"
            ]

            mc_deep = run_monte_carlo(
                tickers=mc_tickers,
                weights=mc_weights,
                initial_value=mc_deep_value,
                years=mc_deep_years,
                simulations=mc_deep_sims,
            )

            paths_df = pd.DataFrame(mc_deep["paths"])

            if mc_stress != 1.0:
                base = paths_df.iloc[0]
                paths_df = base + (paths_df - base) * mc_stress

            final_values = paths_df.iloc[-1]

            if confidence_band == "90%":
                p_low, p_high = 0.05, 0.95
            elif confidence_band == "95%":
                p_low, p_high = 0.025, 0.975
            else:
                p_low, p_high = 0.005, 0.995

            expected_final = final_values.mean()
            median_final = final_values.median()
            p5_final = final_values.quantile(0.05)
            p95_final = final_values.quantile(0.95)
            low_final = final_values.quantile(p_low)
            high_final = final_values.quantile(p_high)

            loss_prob = (final_values < mc_deep_value).mean()
            double_prob = (final_values >= mc_deep_value * 2).mean()
            capital_at_risk = max(0, mc_deep_value - p5_final)

            expected_cagr = ((median_final / mc_deep_value) ** (1 / mc_deep_years) - 1) * 100
            expected_outcome_cagr = ((expected_final / mc_deep_value) ** (1 / mc_deep_years) - 1) * 100
            p5_cagr = ((p5_final / mc_deep_value) ** (1 / mc_deep_years) - 1) * 100
            p95_cagr = ((p95_final / mc_deep_value) ** (1 / mc_deep_years) - 1) * 100

            survival_score = 100
            survival_score -= loss_prob * 45
            survival_score -= min(30, (capital_at_risk / mc_deep_value) * 50)
            survival_score += min(15, double_prob * 20)
            survival_score = max(0, min(100, survival_score))

            survival_label = "Strong" if survival_score >= 75 else "Workable" if survival_score >= 55 else "Fragile"
            survival_color = "#2EE59D" if survival_score >= 75 else "#FFB020" if survival_score >= 55 else "#FF4D6D"

            dispersion_score = min(100, ((high_final - low_final) / mc_deep_value) * 45)
            dispersion_label = "Wide" if dispersion_score >= 70 else "Moderate" if dispersion_score >= 40 else "Tight"
            dispersion_color = "#FF4D6D" if dispersion_score >= 70 else "#FFB020" if dispersion_score >= 40 else "#2EE59D"

            skew_score = ((p95_final - median_final) / median_final)
            kurtosis_proxy = ((p95_final - p5_final) / median_final)

            asymmetry_label = "Favorable" if skew_score > 0.8 else "Balanced" if skew_score > 0.35 else "Negative"
            asymmetry_color = "#2EE59D" if skew_score > 0.8 else "#FFB020" if skew_score > 0.35 else "#FF4D6D"

            simulated_sharpe = expected_cagr / max(1, dispersion_score / 4)

            # -----------------------------
            # Regime / stress logic
            # -----------------------------
            regime_rows = [
                ("Risk-On", 60, expected_cagr, "#2EE59D"),
                ("Recession", 15, expected_cagr - 36.8, "#FF4D6D"),
                ("Inflationary", 10, expected_cagr - 28.4, "#FFB020"),
                ("Crisis", 10, expected_cagr - 43.4, "#FF4D6D"),
                ("Melt-Up", 5, expected_cagr + 17.7, "#3A8DFF"),
            ]

            jump_shock = -20
            vol_spike = mc_stress * 2.5
            correlation_breakdown = "0.85 → 1.00"
            liquidity_shock = -15

            tail_risk_state = "LOW" if loss_prob < 0.05 else "MODERATE" if loss_prob < 0.20 else "HIGH"
            tail_risk_color = "#2EE59D" if loss_prob < 0.05 else "#FFB020" if loss_prob < 0.20 else "#FF4D6D"

            # -----------------------------
            # Top metric strip
            # -----------------------------
            metric_cards = [
                ("Median Outcome", f"${median_final:,.0f}", "#2EE59D"),
                ("Expected Outcome", f"${expected_final:,.0f}", "#E7EEF9"),
                ("5th Percentile", f"${p5_final:,.0f}", "#FF4D6D"),
                ("95th Percentile", f"${p95_final:,.0f}", "#3A8DFF"),
                ("Loss Probability", f"{loss_prob:.1%}", "#2EE59D" if loss_prob < 0.15 else "#FF4D6D"),
                ("Double Probability", f"{double_prob:.1%}", "#2EE59D"),
                ("Capital at Risk", f"${capital_at_risk:,.0f}", "#FF4D6D"),
                ("Sharpe Sim.", f"{simulated_sharpe:.2f}", "#E7EEF9"),
                ("Survival Score", f"{survival_score:.0f}/100", survival_color),
            ]

            metric_html = (
                f'<div style="display:grid; grid-template-columns:repeat(9, minmax(0, 1fr)); '
                f'gap:10px; margin-top:14px;">'
            )

            for label, value, color in metric_cards:
                metric_html += (
                    f'<div class="metric-tile">'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-value" style="color:{color};">{value}</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:10px; overflow:hidden;">'
                            f'<div class="mc-live-bar" style="width:78%; height:100%; background:{color}; border-radius:999px; opacity:0.72;"></div>'
                        f'</div>'
                    f'</div>'
                )

            metric_html += f'</div>'

            st.markdown(metric_html, unsafe_allow_html=True)

            # -----------------------------
            # Main chart row
            # -----------------------------
            chart_col, dist_col, right_col = st.columns([2.1, 1.15, 0.95], gap="medium")

            with chart_col:
                st.markdown("### Capital Pathing")

                median_path = paths_df.median(axis=1)
                low_path = paths_df.quantile(p_low, axis=1)
                high_path = paths_df.quantile(p_high, axis=1)
                p5_path = paths_df.quantile(0.05, axis=1)
                p95_path = paths_df.quantile(0.95, axis=1)

                fig_mc_big = go.Figure()

                fig_mc_big.add_trace(
                    go.Scatter(
                        x=list(range(len(high_path))),
                        y=high_path,
                        mode="lines",
                        line=dict(width=0),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

                fig_mc_big.add_trace(
                    go.Scatter(
                        x=list(range(len(low_path))),
                        y=low_path,
                        mode="lines",
                        fill="tonexty",
                        fillcolor="rgba(58,141,255,0.11)",
                        line=dict(width=0),
                        name=f"{confidence_band} Probability Cone",
                        hoverinfo="skip",
                    )
                )

                sample_paths = paths_df.iloc[:, :min(260, paths_df.shape[1])]

                for col in sample_paths.columns:
                    fig_mc_big.add_trace(
                        go.Scatter(
                            y=sample_paths[col],
                            mode="lines",
                            line=dict(width=1, color="rgba(58,141,255,0.045)"),
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )

                fig_mc_big.add_trace(
                    go.Scatter(
                        y=p95_path,
                        mode="lines",
                        name="95th Path",
                        line=dict(width=3, color="#3A8DFF"),
                    )
                )

                fig_mc_big.add_trace(
                    go.Scatter(
                        y=median_path,
                        mode="lines",
                        name="Median Path",
                        line=dict(width=4, color="#2EE59D"),
                    )
                )

                fig_mc_big.add_trace(
                    go.Scatter(
                        y=p5_path,
                        mode="lines",
                        name="5th Path",
                        line=dict(width=3, color="#FF4D6D"),
                    )
                )

                fig_mc_big.add_hline(
                    y=mc_deep_value,
                    line_dash="dash",
                    line_color="rgba(231,238,249,0.45)",
                    annotation_text="Initial Capital",
                    annotation_position="right",
                    annotation_font=dict(color="rgba(231,238,249,0.72)", size=10),
                )

                fig_mc_big.add_trace(
                    go.Scatter(
                        x=[len(median_path) - 1],
                        y=[median_path.iloc[-1]],
                        mode="markers+text",
                        marker=dict(size=10, color="#2EE59D"),
                        text=[f"${median_final:,.0f}"],
                        textposition="middle right",
                        textfont=dict(color="#2EE59D", size=12),
                        showlegend=False,
                    )
                )

                fig_mc_big.update_layout(
                    height=690,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(3,8,20,0.58)",
                    font=dict(color="#E7EEF9"),
                    margin=dict(l=10, r=10, t=8, b=8),
                    legend=dict(
                        orientation="h",
                        y=1.06,
                        x=0,
                        font=dict(size=11, color="#FFFFFF"),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    hovermode="x unified",
                    xaxis=dict(
                        title="Trading Days",
                        gridcolor="rgba(255,255,255,0.055)",
                        zeroline=False,
                    ),
                    yaxis=dict(
                        title="Portfolio Value",
                        gridcolor="rgba(255,255,255,0.06)",
                        zeroline=False,
                    ),
                )

                st.plotly_chart(fig_mc_big, use_container_width=True)

            with dist_col:
                st.markdown("### Terminal Outcome Distribution")

                fig_dist = go.Figure()

                fig_dist.add_trace(
                    go.Histogram(
                        x=final_values,
                        nbinsx=42,
                        marker=dict(
                            color="#3A8DFF",
                            line=dict(color="rgba(255,255,255,0.08)", width=1),
                        ),
                        opacity=0.78,
                        name="Terminal Outcomes",
                    )
                )

                fig_dist.add_vline(x=mc_deep_value, line_dash="dash", line_color="#E7EEF9", annotation_text="Initial")
                fig_dist.add_vline(x=median_final, line_dash="solid", line_color="#2EE59D", annotation_text="Median")
                fig_dist.add_vline(x=p5_final, line_dash="dot", line_color="#FF4D6D", annotation_text="5th")
                fig_dist.add_vline(x=p95_final, line_dash="dot", line_color="#3A8DFF", annotation_text="95th")

                fig_dist.update_layout(
                    height=690,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(3,8,20,0.58)",
                    font=dict(color="#E7EEF9"),
                    margin=dict(l=10, r=10, t=8, b=8),
                    xaxis=dict(title="Ending Value", gridcolor="rgba(255,255,255,0.055)", zeroline=False),
                    yaxis=dict(title="Frequency", gridcolor="rgba(255,255,255,0.06)", zeroline=False),
                    showlegend=False,
                )

                st.plotly_chart(fig_dist, use_container_width=True)

            with right_col:
                st.markdown("### Regime Outcome Matrix")

                regime_html = (
                    f'<div class="portfolio-card" style="min-height:260px; padding:14px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900;">REGIME MIX</div>'
                            f'<div style="font-size:0.72rem; color:#73CFFF; font-weight:900;">BLEND</div>'
                        f'</div>'
                )

                for name, weight, cagr, color in regime_rows:
                    regime_html += (
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                            f'<div style="display:flex; align-items:center; gap:8px;">'
                                f'<div style="width:9px; height:9px; border-radius:50%; background:{color}; box-shadow:0 0 8px {color};"></div>'
                                f'<span style="color:#E7EEF9; font-size:0.78rem;">{name}</span>'
                            f'</div>'
                            f'<div style="text-align:right;">'
                                f'<div style="color:rgba(231,238,249,0.58); font-size:0.68rem;">{weight}%</div>'
                                f'<div style="color:{color}; font-weight:950; font-size:0.78rem;">CAGR {cagr:.1f}%</div>'
                            f'</div>'
                        f'</div>'
                    )

                regime_html += (
                    f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:12px 0;"></div>'
                    f'<div style="padding:9px; border-radius:10px; background:rgba(58,141,255,0.08); border:1px solid rgba(58,141,255,0.22); text-align:center;">'
                        f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.52);">ACTIVE REGIME INPUT</div>'
                        f'<div style="font-size:0.9rem; font-weight:950; color:#2EE59D; margin-top:4px;">Current Regime Blend</div>'
                    f'</div>'
                    f'</div>'
                )

                st.markdown(regime_html, unsafe_allow_html=True)

                st.markdown("### Tail Shock Analysis")

                tail_html = (
                    f'<div class="portfolio-card" style="min-height:260px; padding:14px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'TAIL / JUMP MODEL'
                        f'</div>'

                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;">'
                            f'<span>Jump Shock (1 Day)</span>'
                            f'<span style="color:#FF4D6D; font-weight:950;">{jump_shock}%</span>'
                        f'</div>'

                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;">'
                            f'<span>Volatility Spike</span>'
                            f'<span style="color:#FFB020; font-weight:950;">{vol_spike:.1f}x</span>'
                        f'</div>'

                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;">'
                            f'<span>Correlation Breakdown</span>'
                            f'<span style="color:#73CFFF; font-weight:950;">{correlation_breakdown}</span>'
                        f'</div>'

                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;">'
                            f'<span>Liquidity Shock</span>'
                            f'<span style="color:#FF4D6D; font-weight:950;">{liquidity_shock}%</span>'
                        f'</div>'

                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:14px 0;"></div>'

                        f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">'
                            f'<div style="padding:10px; border-radius:12px; background:{tail_risk_color}18; border:1px solid {tail_risk_color}44;">'
                                f'<div style="font-size:0.62rem; color:rgba(231,238,249,0.52);">LEFT TAIL RISK</div>'
                                f'<div style="font-size:0.9rem; color:{tail_risk_color}; font-weight:950; margin-top:5px;">{tail_risk_state}</div>'
                            f'</div>'
                            f'<div style="padding:10px; border-radius:12px; background:{asymmetry_color}18; border:1px solid {asymmetry_color}44;">'
                                f'<div style="font-size:0.62rem; color:rgba(231,238,249,0.52);">ASYMMETRY</div>'
                                f'<div style="font-size:0.9rem; color:{asymmetry_color}; font-weight:950; margin-top:5px;">{asymmetry_label}</div>'
                            f'</div>'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(tail_html, unsafe_allow_html=True)

            # -----------------------------
            # Bottom institutional row
            # -----------------------------
            lower_left, lower_mid, lower_drivers, lower_rebalance, lower_ai = st.columns(
                [1.05, 1.25, 1.05, 0.95, 1.45],
                gap="medium"
            )

            with lower_left:
                st.markdown("### Regime Impact Summary")

                regime_impact_html = (
                    f'<div class="portfolio-card" style="min-height:320px; padding:14px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'5Y CAGR BY REGIME'
                        f'</div>'
                )

                for name, weight, cagr, color in regime_rows:
                    width = min(100, max(5, abs(cagr) * 2))

                    regime_impact_html += (
                        f'<div style="margin-bottom:15px;">'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                                f'<span>{name}</span>'
                                f'<span style="color:{color}; font-weight:950;">{cagr:.1f}%</span>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:6px; overflow:hidden;">'
                                f'<div style="width:{width:.1f}%; height:100%; background:{color}; border-radius:999px;"></div>'
                            f'</div>'
                        f'</div>'
                    )

                regime_impact_html += f'</div>'

                st.markdown(regime_impact_html, unsafe_allow_html=True)

            with lower_mid:
                st.markdown("### Stress Test Matrix")

                stress_rows = [
                    ("Base Case", 0.0, 0.0, 0.0),
                    ("Vol Stress 1.5x", -11.8, -18.9, -6.3),
                    ("Vol Stress 2.0x", -21.7, -32.1, -12.4),
                    ("Crash -20%", -24.2, -38.7, -14.6),
                    ("Corr → 1.0", -16.3, -28.4, -9.2),
                    ("Rates +200bp", -6.9, -12.3, -3.1),
                ]

                stress_html = (
                    f'<div class="portfolio-card" style="min-height:320px; padding:14px;">'
                        f'<div style="display:grid; grid-template-columns:1.35fr 0.8fr 0.8fr 0.8fr; gap:8px; '
                        f'color:rgba(231,238,249,0.52); font-size:0.68rem; margin-bottom:10px;">'
                            f'<div>SCENARIO</div>'
                            f'<div>MEDIAN</div>'
                            f'<div>5TH</div>'
                            f'<div>95TH</div>'
                        f'</div>'
                )

                for name, med, fifth, ninety in stress_rows:
                    med_color = "#2EE59D" if med >= 0 else "#FF4D6D"
                    fifth_color = "#2EE59D" if fifth >= 0 else "#FF4D6D"
                    ninety_color = "#2EE59D" if ninety >= 0 else "#FF4D6D"

                    stress_html += (
                        f'<div style="display:grid; grid-template-columns:1.35fr 0.8fr 0.8fr 0.8fr; gap:8px; '
                        f'padding:8px 0; border-top:1px solid rgba(255,255,255,0.06); font-size:0.74rem;">'
                            f'<div style="color:#E7EEF9;">{name}</div>'
                            f'<div style="color:{med_color}; font-weight:900;">{med:+.1f}%</div>'
                            f'<div style="color:{fifth_color}; font-weight:900;">{fifth:+.1f}%</div>'
                            f'<div style="color:{ninety_color}; font-weight:900;">{ninety:+.1f}%</div>'
                        f'</div>'
                    )

                stress_html += f'</div>'

                st.markdown(stress_html, unsafe_allow_html=True)

            with lower_drivers:
                st.markdown("### Outcome Contribution Stack")

                driver_html = (
                    f'<div class="portfolio-card" style="min-height:320px; padding:14px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'CONTRIBUTION PROXY'
                        f'</div>'
                )

                driver_pairs = sorted(
                    zip(mc_tickers, mc_weights),
                    key=lambda x: x[1],
                    reverse=True
                )[:8]

                driver_colors = ["#2EE59D", "#3A8DFF", "#B067FF", "#00D2A8", "#FFB020", "#FF6B6B"]

                for idx, (ticker, weight) in enumerate(driver_pairs):
                    color = driver_colors[idx % len(driver_colors)]
                    width = min(100, max(4, weight * 140))

                    driver_html += (
                        f'<div style="margin-bottom:12px;">'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.76rem;">'
                                f'<span>{ticker}</span>'
                                f'<span style="color:{color}; font-weight:950;">{weight:.1%}</span>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                                f'<div style="width:{width:.1f}%; height:100%; background:{color}; border-radius:999px;"></div>'
                            f'</div>'
                        f'</div>'
                    )

                driver_html += f'</div>'

                st.markdown(driver_html, unsafe_allow_html=True)

            with lower_rebalance:
                st.markdown("### Rebalancing Sensitivity")

                rebalance_rows = [
                    ("Quarterly", expected_cagr, "#2EE59D" if rebalance_mode == "Quarterly" else "#E7EEF9"),
                    ("Monthly", expected_cagr + 0.6, "#3A8DFF" if rebalance_mode == "Monthly" else "#E7EEF9"),
                    ("No Rebalance", expected_cagr - 3.6, "#FFB020" if rebalance_mode == "No Rebalance" else "#E7EEF9"),
                    ("Vol Target", expected_cagr + 2.1, "#73CFFF" if rebalance_mode == "Vol Target" else "#E7EEF9"),
                    ("Risk Parity", expected_cagr - 1.4, "#E7EEF9"),
                ]

                rebalance_html = (
                    f'<div class="portfolio-card" style="min-height:320px; padding:14px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'MEDIAN CAGR'
                        f'</div>'
                )

                for name, cagr, color in rebalance_rows:
                    active_bg = "rgba(46,229,157,0.10)" if name == rebalance_mode else "rgba(255,255,255,0.025)"
                    active_border = "rgba(46,229,157,0.32)" if name == rebalance_mode else "rgba(255,255,255,0.06)"

                    rebalance_html += (
                        f'<div style="display:flex; justify-content:space-between; padding:9px; margin-bottom:8px; '
                        f'border-radius:10px; background:{active_bg}; border:1px solid {active_border}; font-size:0.76rem;">'
                            f'<span>{name}</span>'
                            f'<b style="color:{color};">{cagr:.1f}%</b>'
                        f'</div>'
                    )

                rebalance_html += f'</div>'

                st.markdown(rebalance_html, unsafe_allow_html=True)

            with lower_ai:
                st.markdown("### AI Simulation Desk")

                mc_read = generate_monte_carlo_desk_brief(
                    median_final,
                    p5_final,
                    p95_final,
                    loss_prob,
                    double_prob,
                    capital_at_risk,
                    expected_cagr,
                    survival_score,
                    dispersion_label,
                    mc_deep_years,
                )

                enhanced_mc_context = (
                    f"{mc_read}\n\n"
                    f"[Regime Overlay]\n"
                    f"Risk-On blend carries the strongest simulated CAGR at {regime_rows[0][2]:.1f}%, "
                    f"while crisis and recession states compress the distribution through drawdown and volatility expansion.\n\n"
                    f"[Stress Matrix Read]\n"
                    f"Crash, volatility stress, and correlation breakdown scenarios define the key failure path. "
                    f"The book remains strongest when rebalanced under {rebalance_mode.lower()} discipline."
                )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:320px; padding:16px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                            f'<div style="font-size:0.78rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em;">AI SIMULATION DESK</div>'
                            f'<div style="font-size:0.72rem; color:#2EE59D; font-weight:900;">AI LIVE READ</div>'
                        f'</div>'
                        f'<div style="color:#E7EEF9; font-size:0.84rem; line-height:1.58;">'
                            f'{enhanced_mc_context.replace(chr(10), "<br>")}'
                        f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # -----------------------------
            # Footer
            # -----------------------------
            st.markdown(
                f'<div style="margin-top:14px; padding:10px 14px; border-radius:14px; '
                f'background:rgba(9,23,51,0.72); border:1px solid rgba(255,255,255,0.08); '
                f'display:flex; justify-content:space-between; color:rgba(231,238,249,0.58); font-size:0.76rem;">'
                    f'<span>Model: Hybrid Stochastic · Distribution: Fat-Tail Proxy</span>'
                    f'<span>Simulations: {mc_deep_sims:,}</span>'
                    f'<span>Horizon: {mc_deep_years}Y</span>'
                    f'<span>Rebalancing: {rebalance_mode}</span>'
                    f'<span>Confidence: {confidence_band}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.stop()

        st.markdown(
            f'<div class="portfolio-card" style="margin-top:12px; padding:12px;">'

                f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                    f'<div class="mini-label">MARKET REGIME</div>'

                    f'<div style="width:8px; height:8px; border-radius:50%; '
                    f'background:{market_regime["color"]}; '
                    f'box-shadow:0 0 12px {market_regime["color"]};"></div>'
                f'</div>'

                f'<div style="margin-top:10px; padding:10px; border-radius:14px; '
                f'background:linear-gradient(135deg, rgba(46,229,157,0.08), rgba(58,141,255,0.03)); '
                f'border:1px solid {market_regime["color"]};">'

                    f'<div style="color:{market_regime["color"]}; '
                    f'font-size:1.05rem; font-weight:800;">'

                        f'{market_regime["regime"]}'

                    f'</div>'

                f'</div>'

                f'<div style="margin-top:12px; display:flex; justify-content:space-between; '
                f'font-size:0.72rem;">'

                    f'<span style="color:rgba(231,238,249,0.55);">Status</span>'

                    f'<span style="color:#2EE59D;">LIVE</span>'

                f'</div>'

            f'</div>',
            unsafe_allow_html=True
        )
        if selected_view == "Market Regime Engine":

            probs = market_regime["probabilities"]

            # -----------------------------
            # Deep analytics
            # -----------------------------
            regime_score = market_regime["score"]
            vix = market_regime["vix"]
            spy_6m = market_regime["spy_return"]
            qqq_6m = market_regime["qqq_return"]
            tlt_6m = market_regime["tlt_return"]
            gld_6m = market_regime["gld_return"]

            regime_confidence = min(95, max(35, regime_score * 0.85 + probs["Risk-On"] * 0.25))
            regime_stability = min(95, max(20, 100 - abs(probs["Risk-On"] - probs["Late Cycle"]) * 0.7))

            equity_signal = "Bullish" if spy_6m > 5 else "Weak" if spy_6m < -5 else "Neutral"
            growth_signal = "Leading" if qqq_6m > spy_6m else "Lagging"
            duration_signal = "Stress Hedge Bid" if tlt_6m > spy_6m else "No Stress Bid"
            gold_signal = "Inflation Hedge Bid" if gld_6m > 5 else "Neutral"
            vol_signal = "Contained" if vix < 18 else "Elevated" if vix < 25 else "Stress"

            vix_risk = "LOW" if vix < 18 else "MEDIUM" if vix < 25 else "HIGH"
            qqq_risk = "LOW" if qqq_6m > spy_6m else "MEDIUM"
            spy_risk = "LOW" if spy_6m > 5 else "MEDIUM" if spy_6m > 0 else "HIGH"

            ai_regime_text = generate_market_regime_brief(
                market_regime,
                portfolio_type,
                risk_level,
                allocation,
                assets
            )

            # -----------------------------
            # Header
            # -----------------------------
            st.markdown(
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'

                        f'<div>'
                            f'<div style="font-size:1.75rem; font-weight:950; color:#E7EEF9;">'
                                f'Market Regime Engine'
                            f'</div>'

                            f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">'
                                f'Institutional macro regime classification and transition analysis.'
                            f'</div>'
                        f'</div>'

                        f'<div style="text-align:right;">'
                            f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.52);">MACRO FEED</div>'
                            f'<div style="font-size:1rem; color:#2EE59D; font-weight:900;">LIVE</div>'
                        f'</div>'

                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # -----------------------------
            # Top metrics
            # -----------------------------
            regime_cols = st.columns(5, gap="medium")

            top_metrics = [
                ("Current Regime", market_regime["regime"], market_regime["color"]),
                ("Regime Score", f'{market_regime["score"]:.0f}/100', "#E7EEF9"),
                ("VIX", f'{market_regime["vix"]:.1f}', "#FFB020"),
                ("SPY 6M", f'{market_regime["spy_return"]:+.1f}%', "#2EE59D"),
                ("QQQ 6M", f'{market_regime["qqq_return"]:+.1f}%', "#4DA3FF"),
            ]

            for i, (label, value, color) in enumerate(top_metrics):
                with regime_cols[i]:
                    st.markdown(
                        f'<div class="metric-tile">'
                            f'<div class="metric-label">{label}</div>'
                            f'<div class="metric-value" style="color:{color};">{value}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            # -----------------------------
            # Regime Transition Meter
            # -----------------------------
            st.markdown("### Regime Transition Positioning")

            transition_position = probs["Risk-On"] * 1.0 + probs["Late Cycle"] * 0.55 + probs["Risk-Off"] * 0.2
            transition_position = min(100, max(0, transition_position))

            st.markdown(
                f'<div class="portfolio-card" style="padding:18px; min-height:110px;">'

                    f'<div style="display:flex; justify-content:space-between; margin-bottom:12px;">'

                        f'<span style="font-size:0.78rem; letter-spacing:0.08em; color:rgba(231,238,249,0.55);">'
                            f'REGIME TRANSITION MODEL'
                        f'</span>'

                        f'<span style="font-size:0.85rem; font-weight:900; color:#2EE59D;">'
                            f'RISK-ON DOMINANCE'
                        f'</span>'

                    f'</div>'

                    f'<div style="position:relative; margin-top:14px;">'

                        f'<div style="height:14px; border-radius:999px; overflow:hidden; display:flex;">'

                            f'<div style="width:40%; background:#2EE59D;"></div>'
                            f'<div style="width:25%; background:#FFB020;"></div>'
                            f'<div style="width:20%; background:#3A8DFF;"></div>'
                            f'<div style="width:15%; background:#FF4D6D;"></div>'

                        f'</div>'

                        f'<div style="position:absolute; left:{transition_position}%; top:-6px; transform:translateX(-50%);">'
                            f'<div style="width:4px; height:26px; background:white; border-radius:999px; box-shadow:0 0 12px white;"></div>'
                        f'</div>'

                    f'</div>'

                    f'<div style="display:flex; justify-content:space-between; margin-top:10px; font-size:0.72rem; color:rgba(231,238,249,0.52);">'

                        f'<span>Risk-On</span>'
                        f'<span>Late Cycle</span>'
                        f'<span>Risk-Off</span>'
                        f'<span>Recession</span>'

                    f'</div>'

                f'</div>',
                unsafe_allow_html=True
            )

            # -----------------------------
            # Confidence strip
            # -----------------------------
            confidence_cols = st.columns(4, gap="medium")

            confidence_data = [
                ("Trend Strength", f"{regime_confidence:.0f}%", "#2EE59D"),
                ("Regime Stability", f"{regime_stability:.0f}%", "#4DA3FF"),
                ("Volatility State", "Contained" if vix < 18 else "Elevated", "#F7B500"),
                ("Cross-Asset Confirmation", "Strong", "#00E5FF")
            ]

            for i, (label, value, color) in enumerate(confidence_data):

                with confidence_cols[i]:

                    st.markdown(
                        f'<div class="portfolio-card" style="min-height:95px; padding:16px; border:1px solid rgba(255,255,255,0.06); background:linear-gradient(135deg, rgba(8,18,40,0.95), rgba(5,10,24,0.95));">'

                            f'<div style="font-size:11px; letter-spacing:1px; text-transform:uppercase; color:rgba(231,238,249,0.58); margin-bottom:8px;">'
                                f'{label}'
                            f'</div>'

                            f'<div style="font-size:28px; font-weight:900; color:{color}; line-height:1;">'
                                f'{value}'
                            f'</div>'

                            f'<div style="margin-top:10px; height:6px; border-radius:999px; background:rgba(255,255,255,0.06); overflow:hidden;">'
                                f'<div style="width:78%; height:100%; background:{color}; border-radius:999px; box-shadow:0 0 12px {color};"></div>'
                            f'</div>'

                        f'</div>',
                        unsafe_allow_html=True
                    )

            # -----------------------------
            # Main workspace
            # -----------------------------
            left_workspace, center_workspace, right_workspace = st.columns([1.2, 1.55, 0.95], gap="medium")

            # -----------------------------
            # LEFT
            # -----------------------------
            with left_workspace:

                st.markdown("### Regime Timeline Engine")

                timeline_data = [
                    ("T-5", "Risk-On", "#2EE59D"),
                    ("T-4", "Risk-On", "#2EE59D"),
                    ("T-3", "Risk-On", "#2EE59D"),
                    ("T-2", "Late Cycle", "#FFB020"),
                    ("T-1", "Risk-On", "#2EE59D"),
                    ("Now", market_regime["regime"], market_regime["color"]),
                ]

                timeline_html = ""

                for label, regime_name, color in timeline_data:
                    timeline_html += (
                        f'<div style="flex:1; text-align:center;">'
                            f'<div style="height:12px; border-radius:999px; background:{color}; box-shadow:0 0 10px {color};"></div>'
                            f'<div style="margin-top:7px; font-size:0.66rem; color:rgba(231,238,249,0.50);">{label}</div>'
                            f'<div style="margin-top:3px; font-size:0.66rem; color:{color}; font-weight:800;">{regime_name}</div>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div class="portfolio-card" style="padding:16px; min-height:125px;">'
                        f'<div style="display:flex; gap:8px; align-items:flex-start;">'
                            f'{timeline_html}'
                        f'</div>'
                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:14px 0 10px 0;"></div>'
                        f'<div style="display:flex; justify-content:space-between; font-size:0.74rem; color:rgba(231,238,249,0.58);">'
                            f'<span>Regime persistence: <b style="color:#2EE59D;">High</b></span>'
                            f'<span>Transition drift: <b style="color:#FFB020;">Moderate</b></span>'
                        f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.success("Checkpoint 1")
                st.markdown("### Regime Probability")

                fig_regime = go.Figure()

                fig_regime.add_trace(
                    go.Bar(
                        x=list(probs.keys()),
                        y=list(probs.values()),
                        marker=dict(
                            color=["#2EE59D", "#FFB020", "#3A8DFF", "#FF4D6D"]
                        ),
                    )
                )

                fig_regime.update_layout(
                    height=300,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E7EEF9"),
                    margin=dict(l=10, r=10, t=10, b=10),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", ticksuffix="%"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                    showlegend=False,
                )

                st.plotly_chart(fig_regime, use_container_width=True)

                st.markdown("### Transition Risk")

                risk_rows = [
                    ("VIX Expansion Risk", vix_risk, 22, "#FFB020"),
                    ("QQQ Breakdown Risk", qqq_risk, 18, "#4DA3FF"),
                    ("SPY Trend Failure", spy_risk, 12, "#FF4D6D"),
                ]

                risk_html = ""

                for label, status, level, color in risk_rows:
                    risk_html += (
                        f'<div style="margin-bottom:18px;">'
                            f'<div style="display:flex; justify-content:space-between; margin-bottom:6px;">'
                                f'<span>{label}</span>'
                                f'<span style="color:{color}; font-weight:900;">{status}</span>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.06); overflow:hidden;">'
                                f'<div style="width:{level}%; height:100%; background:{color}; border-radius:999px; box-shadow:0 0 10px {color};"></div>'
                            f'</div>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:220px;">'

                        f'{risk_html}'

                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:14px 0;"></div>'

                        f'<div style="color:rgba(231,238,249,0.65); font-size:0.8rem; line-height:1.6;">'
                            f'Engine monitoring transition pressure across volatility, growth leadership, and defensive asset rotation.'
                        f'</div>'

                    f'</div>',
                    unsafe_allow_html=True
                )

            # -----------------------------
            # CENTER
            # -----------------------------
            with center_workspace:

                st.markdown("### AI Desk Interpretation")

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:540px; padding:20px;">'

                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">'

                            f'<div style="font-size:0.78rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em;">'
                                f'INTERNAL MACRO DESK'
                            f'</div>'

                            f'<div style="color:#2EE59D; font-size:0.74rem; font-weight:900;">LIVE</div>'

                        f'</div>'

                        f'<div style="color:rgba(231,238,249,0.84); font-size:0.93rem; line-height:1.7;">'
                            f'{ai_regime_text.replace(chr(10), "<br>")}'
                        f'</div>'

                    f'</div>',
                    unsafe_allow_html=True
                )

            # -----------------------------
            # RIGHT
            # -----------------------------
            with right_workspace:

                st.markdown("### Signal Stack")

                signal_rows = [
                    ("Equity Trend", equity_signal, "#2EE59D"),
                    ("Growth Leadership", growth_signal, "#4DA3FF"),
                    ("Duration", duration_signal, "#FFB020"),
                    ("Gold", gold_signal, "#F7B500"),
                    ("Volatility", vol_signal, "#FF4D6D"),
                ]

                signal_html = ""

                for label, value, color in signal_rows:

                    signal_html += (
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:12px;">'
                            f'<span>{label}</span>'
                            f'<span style="color:{color}; font-weight:900;">{value}</span>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:260px;">'
                        f'{signal_html}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                st.markdown("### Cross-Asset Read")

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:250px;">'

                        f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">'

                            f'<div style="padding:10px; border-radius:10px; background:rgba(46,229,157,0.08); text-align:center;">'
                                f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.52);">EQUITIES</div>'
                                f'<div style="font-size:1rem; font-weight:900; color:#2EE59D;">BULLISH</div>'
                            f'</div>'

                            f'<div style="padding:10px; border-radius:10px; background:rgba(255,176,32,0.08); text-align:center;">'
                                f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.52);">BONDS</div>'
                                f'<div style="font-size:1rem; font-weight:900; color:#FFB020;">NEUTRAL</div>'
                            f'</div>'

                            f'<div style="padding:10px; border-radius:10px; background:rgba(58,141,255,0.08); text-align:center;">'
                                f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.52);">VOLATILITY</div>'
                                f'<div style="font-size:1rem; font-weight:900; color:#4DA3FF;">STABLE</div>'
                            f'</div>'

                            f'<div style="padding:10px; border-radius:10px; background:rgba(247,181,0,0.08); text-align:center;">'
                                f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.52);">GOLD</div>'
                                f'<div style="font-size:1rem; font-weight:900; color:#F7B500;">HEDGE BID</div>'
                            f'</div>'

                        f'</div>'

                    f'</div>',
                    unsafe_allow_html=True
                )

                st.markdown("### Macro Factor Heatmap")
                macro_factors = [
                    ("Liquidity", "Supportive", "#2EE59D"),
                    ("Growth", "Strong", "#2EE59D"),
                    ("Inflation", "Sticky", "#FFB020"),
                    ("Rates", "Neutral", "#F7B500"),
                    ("Credit", "Calm", "#2EE59D"),
                    ("Volatility", "Contained", "#4DA3FF"),
                    ("USD", "Neutral", "#94A3B8"),
                    ("Commodities", "Bid", "#FFB020"),
                ]

                factor_heatmap_html = ""

                for factor, state, color in macro_factors:
                    factor_heatmap_html += (
                        f'<div style="padding:9px; border-radius:10px; background:{color}18; border:1px solid {color}55;">'
                            f'<div style="font-size:0.62rem; color:rgba(231,238,249,0.55); text-transform:uppercase; letter-spacing:0.06em;">{factor}</div>'
                            f'<div style="font-size:0.82rem; font-weight:950; color:{color}; margin-top:4px;">{state}</div>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:210px; padding:14px;">'
                        f'<div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:8px;">'
                            f'{factor_heatmap_html}'
                        f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )           

            st.stop()


        if selected_view == "Risk Engine":
            risk_engine = calculate_allocation_risk_engine(
                recommendations,
                st.session_state.allocation_horizon
            )

            st.markdown(
                """
                <style>
                @keyframes shockPulse {
                    0% { opacity: 0.72; filter: brightness(0.95); }
                    50% { opacity: 1; filter: brightness(1.25); }
                    100% { opacity: 0.72; filter: brightness(0.95); }
                }
                .shock-bar {
                    animation: shockPulse 2.2s ease-in-out infinite;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            header_html = (
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<div>'
                            f'<div style="font-size:1.75rem; font-weight:950; color:#E7EEF9;">Risk Engine</div>'
                            f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">'
                                f'Institutional portfolio risk analysis tied to the active allocation.'
                            f'</div>'
                        f'</div>'
                        f'<div style="text-align:right;">'
                            f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.52);">RISK MODEL</div>'
                            f'<div style="font-size:1rem; color:#2EE59D; font-weight:900;">LIVE</div>'
                        f'</div>'
                    f'</div>'
                f'</div>'
            )

            st.markdown(header_html, unsafe_allow_html=True)

            if risk_engine is None:
                st.warning("Risk Engine data unavailable. Try again once market data loads.")
                st.stop()

            exposure_df = risk_engine["exposure_df"].copy()

            # -----------------------------
            # Extra institutional risk signals
            # -----------------------------
            tail_fragility_index = 0
            tail_fragility_index += min(30, abs(risk_engine["cvar_95"]) * 4)
            tail_fragility_index += min(25, abs(risk_engine["max_drawdown"]) * 0.6)
            tail_fragility_index += min(20, max(0, risk_engine["downside_capture"] - 1) * 35)
            tail_fragility_index += min(15, max(0, risk_engine["beta"] - 1) * 25)
            tail_fragility_index += min(10, max(0, risk_engine["top_3_weight"] - 50) * 0.35)
            tail_fragility_index = max(0, min(100, tail_fragility_index))

            tail_label = "High" if tail_fragility_index >= 70 else "Elevated" if tail_fragility_index >= 45 else "Controlled"
            tail_color = "#FF4D6D" if tail_fragility_index >= 70 else "#FFB020" if tail_fragility_index >= 45 else "#2EE59D"

            liquidity_stress_score = 0
            liquidity_stress_score += min(35, risk_engine["annual_vol"] * 0.9)
            liquidity_stress_score += min(25, risk_engine["top_weight"] * 0.6)
            liquidity_stress_score += min(20, abs(risk_engine["cvar_95"]) * 3)
            liquidity_stress_score += min(20, tail_fragility_index * 0.2)
            liquidity_stress_score = max(0, min(100, liquidity_stress_score))

            liquidity_label = "Thin" if liquidity_stress_score >= 70 else "Watch" if liquidity_stress_score >= 45 else "Stable"
            liquidity_color = "#FF4D6D" if liquidity_stress_score >= 70 else "#FFB020" if liquidity_stress_score >= 45 else "#2EE59D"

            convexity_score = 0
            convexity_score += min(35, risk_engine["annual_vol"] * 0.8)
            convexity_score += min(25, max(0, risk_engine["beta"] - 1) * 30)
            convexity_score += min(25, abs(risk_engine["cvar_95"]) * 3.5)
            convexity_score += min(15, max(0, risk_engine["downside_capture"] - 1) * 25)
            convexity_score = max(0, min(100, convexity_score))

            convexity_label = "Negative Convexity" if convexity_score >= 70 else "Convexity Watch" if convexity_score >= 45 else "Contained"
            convexity_color = "#FF4D6D" if convexity_score >= 70 else "#FFB020" if convexity_score >= 45 else "#2EE59D"

            regime_name = market_regime.get("regime", "Mixed / Transition") if isinstance(market_regime, dict) else "Mixed / Transition"

            if "Risk-Off" in regime_name or "Recession" in regime_name:
                regime_multiplier = 1.45
                regime_tag = "Risk-Off Shock"
            elif "Late" in regime_name or "Transition" in regime_name:
                regime_multiplier = 1.20
                regime_tag = "Transition Shock"
            else:
                regime_multiplier = 1.00
                regime_tag = "Normal Shock"

            regime_spy_down_5 = risk_engine["stress_market_down_5"] * regime_multiplier
            liquidity_drag = -1 * (liquidity_stress_score / 100) * 4
            convexity_drag = -1 * (convexity_score / 100) * 5

            # Hidden correlation clusters
            cluster_rows_html = ""
            try:
                corr = calculate_allocation_correlation_matrix(
                    recommendations,
                    st.session_state.allocation_horizon
                )

                hidden_clusters = []

                if corr is not None:
                    for i, t1 in enumerate(corr.columns):
                        for t2 in corr.columns[i + 1:]:
                            pair_corr = float(corr.loc[t1, t2])
                            if pair_corr >= 0.75:
                                hidden_clusters.append((t1, t2, pair_corr))

                hidden_clusters = sorted(hidden_clusters, key=lambda x: x[2], reverse=True)[:4]

                if hidden_clusters:
                    for t1, t2, pair_corr in hidden_clusters:
                        c_color = "#FF4D6D" if pair_corr >= 0.90 else "#FFB020"

                        cluster_rows_html += (
                            f'<div style="padding:9px 10px; margin-bottom:8px; border-radius:12px; '
                            f'background:linear-gradient(90deg, {c_color}22, rgba(9,23,51,0.76)); border:1px solid {c_color}44;">'
                                f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                                    f'<div style="font-size:0.78rem; font-weight:950; color:#E7EEF9;">{t1} / {t2}</div>'
                                    f'<div style="font-size:0.9rem; font-weight:950; color:{c_color};">{pair_corr:.2f}</div>'
                                f'</div>'
                                f'<div style="height:5px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:7px; overflow:hidden;">'
                                    f'<div style="width:{pair_corr * 100:.1f}%; height:100%; background:{c_color}; border-radius:999px;"></div>'
                                f'</div>'
                            f'</div>'
                        )
                else:
                    cluster_rows_html = (
                        f'<div style="color:rgba(231,238,249,0.62); font-size:0.82rem; line-height:1.6;">'
                        f'No major hidden correlation clusters detected above 0.75.'
                        f'</div>'
                    )
            except Exception:
                cluster_rows_html = (
                    f'<div style="color:rgba(231,238,249,0.62); font-size:0.82rem; line-height:1.6;">'
                    f'Correlation cluster scan unavailable.'
                    f'</div>'
                )

            # Factor decomposition proxy
            tickers_for_factor = exposure_df["Ticker"].tolist() if not exposure_df.empty else []

            factor_scores = {
                "Market Beta": min(100, max(0, risk_engine["beta"] * 75)),
                "Growth / Tech": 0,
                "Duration Hedge": 0,
                "Crypto / High Beta": 0,
                "Defensive Hedge": 0,
            }

            for _, row in exposure_df.iterrows():
                ticker = str(row["Ticker"])
                weight = float(row["Weight"])

                if ticker in ["QQQ", "SMH", "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "TSLA"]:
                    factor_scores["Growth / Tech"] += weight

                if ticker in ["TLT", "IEF", "SHY"]:
                    factor_scores["Duration Hedge"] += weight

                if ticker in ["MSTR", "BTC-USD", "ETH-USD", "COIN"]:
                    factor_scores["Crypto / High Beta"] += weight

                if ticker in ["GLD", "IAU", "SHY", "TLT"]:
                    factor_scores["Defensive Hedge"] += weight

            factor_rows_html = ""

            for factor, score in factor_scores.items():
                score = min(100, score)
                f_color = "#FF4D6D" if score >= 65 else "#FFB020" if score >= 35 else "#2EE59D"

                factor_rows_html += (
                    f'<div style="margin-bottom:9px;">'
                        f'<div style="display:flex; justify-content:space-between; font-size:0.74rem;">'
                            f'<span style="color:#E7EEF9;">{factor}</span>'
                            f'<span style="color:{f_color}; font-weight:950;">{score:.0f}</span>'
                        f'</div>'
                        f'<div style="height:5px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                            f'<div style="width:{score:.1f}%; height:100%; background:{f_color}; border-radius:999px;"></div>'
                        f'</div>'
                    f'</div>'
                )

                     # -----------------------------
            # Top risk metric strip — wide terminal layout
            # -----------------------------
            metric_cards = [
                ("Volatility", f'{risk_engine["annual_vol"]:.1f}%', "#E7EEF9"),
                ("Max Drawdown", f'{risk_engine["max_drawdown"]:.1f}%', "#FF4D6D"),
                ("VaR 95%", f'{risk_engine["var_95"]:.2f}%', "#FFB020"),
                ("CVaR 95%", f'{risk_engine["cvar_95"]:.2f}%', "#FF4D6D"),
                ("Beta vs SPY", f'{risk_engine["beta"]:.2f}', "#73CFFF"),
                ("Survivability", f'{risk_engine["survivability_score"]:.0f}/100', "#2EE59D"),
                ("Tail Fragility", f'{tail_fragility_index:.0f}/100', tail_color),
                ("Liquidity Stress", f'{liquidity_stress_score:.0f}/100', liquidity_color),
                ("Convexity", f'{convexity_score:.0f}/100', convexity_color),
            ]

            metric_html = '<div style="display:grid; grid-template-columns:repeat(9, minmax(0, 1fr)); gap:10px; margin-top:12px; margin-bottom:14px;">'

            for label, value, color in metric_cards:
                metric_html += (
                    f'<div class="metric-tile" style="min-height:105px; padding:14px;">'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-value" style="color:{color}; font-size:1.35rem;">{value}</div>'
                        f'<div style="height:24px; margin-top:12px; border-radius:8px; '
                        f'background:linear-gradient(90deg, {color}55, rgba(255,255,255,0.04)); '
                        f'border-bottom:1px solid {color}66;"></div>'
                    f'</div>'
                )

            metric_html += '</div>'
            st.markdown(metric_html, unsafe_allow_html=True)

            # -----------------------------
            # Row 1: chart + risk stack
            # -----------------------------
            chart_col, stack_col = st.columns([1.55, 1.4], gap="medium")

            with chart_col:
                if "risk_monitor_timeframe" not in st.session_state:
                    st.session_state.risk_monitor_timeframe = "MAX"

                title_col, tf_col = st.columns([3, 1.25], gap="small")

                with title_col:
                    st.markdown(
                        '<div style="font-size:1.05rem; font-weight:950; color:#E7EEF9; margin-top:6px;">Rolling Risk Monitor</div>',
                        unsafe_allow_html=True
                    )

                with tf_col:
                    tf_buttons = st.columns(4)

                    for i, tf in enumerate(["1Y", "2Y", "3Y", "MAX"]):
                        with tf_buttons[i]:
                            if st.button(
                                tf,
                                key=f"risk_monitor_tf_{tf}",
                                use_container_width=True,
                                type="primary" if st.session_state.risk_monitor_timeframe == tf else "secondary",
                            ):
                                st.session_state.risk_monitor_timeframe = tf
                                st.rerun()

                rolling_vol_series = risk_engine["rolling_vol"].dropna()
                rolling_dd_series = risk_engine["rolling_drawdown"].dropna()

                selected_tf = st.session_state.risk_monitor_timeframe

                if selected_tf != "MAX":
                    years_back = int(selected_tf.replace("Y", ""))
                    cutoff_date = rolling_vol_series.index.max() - pd.DateOffset(years=years_back)

                    rolling_vol_series = rolling_vol_series[
                        rolling_vol_series.index >= cutoff_date
                    ]

                    rolling_dd_series = rolling_dd_series[
                        rolling_dd_series.index >= cutoff_date
                    ]

                selected_tf = st.session_state.risk_monitor_timeframe

                if selected_tf != "MAX":
                    years_back = int(selected_tf.replace("Y", ""))
                    cutoff_date = rolling_vol_series.index.max() - pd.DateOffset(years=years_back)

                    rolling_vol_series = rolling_vol_series[
                        rolling_vol_series.index >= cutoff_date
                    ]

                    rolling_dd_series = rolling_dd_series[
                        rolling_dd_series.index >= cutoff_date
                    ]

                current_vol = float(rolling_vol_series.iloc[-1])
                current_dd = float(rolling_dd_series.iloc[-1])

                vol_regime = "Elevated" if current_vol >= 25 else "Watch" if current_vol >= 18 else "Controlled"
                vol_regime_color = "#FF4D6D" if current_vol >= 25 else "#FFB020" if current_vol >= 18 else "#2EE59D"

                dd_state = "Stress" if current_dd <= -20 else "Warning" if current_dd <= -10 else "Contained"
                dd_state_color = "#FF4D6D" if current_dd <= -20 else "#FFB020" if current_dd <= -10 else "#2EE59D"
                monitor_cards = (
                    f'<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; margin-bottom:12px;">'
                        f'<div class="portfolio-card" style="padding:12px; min-height:88px;">'
                            f'<div style="font-size:0.70rem; color:rgba(231,238,249,0.55); letter-spacing:0.08em; font-weight:900;">21D VOLATILITY</div>'
                            f'<div style="font-size:1.45rem; font-weight:950; color:#3A8DFF; margin-top:7px;">{current_vol:.1f}%</div>'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.55);">Annualized</div>'
                        f'</div>'
                        f'<div class="portfolio-card" style="padding:12px; min-height:88px;">'
                            f'<div style="font-size:0.70rem; color:rgba(231,238,249,0.55); letter-spacing:0.08em; font-weight:900;">CURRENT DRAWDOWN</div>'
                            f'<div style="font-size:1.45rem; font-weight:950; color:#FF4D6D; margin-top:7px;">{current_dd:.1f}%</div>'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.55);">From peak</div>'
                        f'</div>'
                        f'<div class="portfolio-card" style="padding:12px; min-height:88px;">'
                            f'<div style="font-size:0.70rem; color:rgba(231,238,249,0.55); letter-spacing:0.08em; font-weight:900;">VOL REGIME</div>'
                            f'<div style="font-size:1.35rem; font-weight:950; color:{vol_regime_color}; margin-top:8px;">{vol_regime}</div>'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.55);">Realized risk state</div>'
                        f'</div>'
                        f'<div class="portfolio-card" style="padding:12px; min-height:88px;">'
                            f'<div style="font-size:0.70rem; color:rgba(231,238,249,0.55); letter-spacing:0.08em; font-weight:900;">DRAWDOWN STATE</div>'
                            f'<div style="font-size:1.35rem; font-weight:950; color:{dd_state_color}; margin-top:8px;">{dd_state}</div>'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.55);">Live risk posture</div>'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(monitor_cards, unsafe_allow_html=True)

                fig_risk = go.Figure()

                fig_risk.add_hrect(y0=-10, y1=0, yref="y2", fillcolor="rgba(255,176,32,0.07)", line_width=0)
                fig_risk.add_hrect(y0=-20, y1=-10, yref="y2", fillcolor="rgba(255,77,109,0.08)", line_width=0)
                fig_risk.add_hrect(y0=-40, y1=-20, yref="y2", fillcolor="rgba(255,77,109,0.14)", line_width=0)

                for level, label, color in [
                    (-10, "WARNING", "#FFB020"),
                    (-20, "HIGH RISK", "#FF4D6D"),
                    (-30, "EXTREME", "#FF4D6D"),
                ]:
                     fig_risk.add_hline(

                        y=level,

                        yref="y2",

                        line_dash="dash",

                        line_color=color,

                        opacity=0.65,

                        annotation_text=label,

                        annotation_position="right",

                        annotation_font=dict(color=color, size=10),

                    )

                fig_risk.add_trace(

                    go.Scatter(

                        x=rolling_vol_series.index,

                        y=rolling_vol_series,

                        mode="lines",

                        name="Rolling Volatility",

                        line=dict(color="#3A8DFF", width=4),

                    )

                )

                fig_risk.add_trace(

                    go.Scatter(

                        x=rolling_vol_series.index,

                        y=rolling_vol_series,

                        mode="lines",

                        name="Vol Glow",

                        line=dict(color="rgba(58,141,255,0.22)", width=10),

                        hoverinfo="skip",

                        showlegend=False,

                    )

                )

                fig_risk.add_trace(

                    go.Scatter(

                        x=rolling_dd_series.index,

                        y=rolling_dd_series,

                        mode="lines",

                        name="Rolling Drawdown",

                        line=dict(color="#FF4D6D", width=3),

                        yaxis="y2",

                    )

                )

                fig_risk.add_trace(

                    go.Scatter(

                        x=[rolling_vol_series.index[-1]],

                        y=[current_vol],

                        mode="markers+text",

                        name="Latest Vol",

                        marker=dict(size=10, color="#3A8DFF"),

                        text=[f"{current_vol:.1f}%"],

                        textposition="middle right",

                        textfont=dict(color="#3A8DFF", size=12),

                        showlegend=False,

                    )

                )

                fig_risk.add_trace(

                    go.Scatter(

                        x=[rolling_dd_series.index[-1]],

                        y=[current_dd],

                        mode="markers+text",

                        name="Latest DD",

                        marker=dict(size=10, color="#FF4D6D"),

                        text=[f"{current_dd:.1f}%"],

                        textposition="middle right",

                        textfont=dict(color="#FF4D6D", size=12),

                        yaxis="y2",

                        showlegend=False,

                    )

                )

                fig_risk.update_layout(

                    height=430,

                    paper_bgcolor="rgba(0,0,0,0)",

                    plot_bgcolor="rgba(3,8,20,0.62)",

                    font=dict(color="#E7EEF9"),

                    margin=dict(l=12, r=20, t=18, b=10),

                    legend=dict(

                        orientation="h",

                        y=1.08,

                        x=0,

                        font=dict(size=11, color="#FFFFFF"),

                        bgcolor="rgba(0,0,0,0)",

                    ),

                    hovermode="x unified",

                    xaxis=dict(

                        gridcolor="rgba(255,255,255,0.055)",

                        zeroline=False,

                    ),

                    yaxis=dict(

                        title="Volatility % Ann.",

                        gridcolor="rgba(255,255,255,0.06)",

                        ticksuffix="%",

                        color="#3A8DFF",

                        zeroline=False,

                    ),

                    yaxis2=dict(

                        title="Drawdown %",

                        overlaying="y",

                        side="right",

                        gridcolor="rgba(255,255,255,0)",

                        ticksuffix="%",

                        color="#FF4D6D",

                        range=[-40, 0],

                        zeroline=False,
                    ),
                )

                st.plotly_chart(fig_risk, use_container_width=True)

                st.markdown(
                    f'<div class="portfolio-card" style="padding:9px 12px; margin-top:8px; display:flex; justify-content:space-between; '
                    f'color:rgba(231,238,249,0.58); font-size:0.72rem;">'
                        f'<span>Latest Update: live on refresh</span>'
                        f'<span>Volatility = 21D annualized std dev</span>'
                        f'<span>Drawdown = peak-to-trough loss</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with stack_col:
                st.markdown("### Risk Stack")

                gauge_degrees = risk_engine["survivability_score"] * 3.6
                overall_stress_impact = (
                    risk_engine["stress_market_down_5"]
                    + regime_spy_down_5
                    + liquidity_drag
                    + convexity_drag
                )

                risk_stack_html = (
                    f'<div class="portfolio-card" style="min-height:430px; padding:18px;">'

                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                            f'<div style="font-size:0.78rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900;">RISK STACK</div>'
                            f'<div style="font-size:0.72rem; color:#2EE59D; font-weight:900;">RISK MODEL&nbsp;&nbsp;LIVE</div>'
                        f'</div>'

                        f'<div style="display:grid; grid-template-columns:0.78fr 1.12fr 0.9fr; gap:14px; align-items:center;">'

                            f'<div style="text-align:center;">'
                                f'<div style="margin:0 auto; width:138px; height:138px; border-radius:50%; '
                                f'background:conic-gradient(#2EE59D 0deg, #2EE59D {gauge_degrees:.0f}deg, rgba(255,255,255,0.08) {gauge_degrees:.0f}deg); '
                                f'display:flex; align-items:center; justify-content:center;">'
                                    f'<div style="width:96px; height:96px; border-radius:50%; background:#091733; '
                                    f'display:flex; align-items:center; justify-content:center; flex-direction:column;">'
                                        f'<div style="font-size:1.85rem; font-weight:950; color:#E7EEF9;">{risk_engine["survivability_score"]:.0f}</div>'
                                        f'<div style="font-size:0.62rem; color:rgba(231,238,249,0.55);">/100</div>'
                                    f'</div>'
                                f'</div>'
                                f'<div style="margin-top:10px; font-size:0.85rem; font-weight:950; color:#2EE59D;">'
                                    f'{risk_engine["survivability_label"]} SURVIVABILITY'
                                f'</div>'
                            f'</div>'

                            f'<div style="background:rgba(255,255,255,0.035); border-radius:14px; padding:12px;">'
                                f'<div style="display:flex; justify-content:space-between; margin-bottom:7px;"><span>Downside Capture</span><b>{risk_engine["downside_capture"]:.2f}x</b></div>'
                                f'<div style="display:flex; justify-content:space-between; margin-bottom:7px;"><span>SPY Correlation</span><b>{risk_engine["corr_spy"]:.2f}</b></div>'
                                f'<div style="display:flex; justify-content:space-between; margin-bottom:7px;"><span>Top Holding</span><b>{risk_engine["top_weight"]:.1f}%</b></div>'
                                f'<div style="display:flex; justify-content:space-between; margin-bottom:7px;"><span>Top 3 Holdings</span><b>{risk_engine["top_3_weight"]:.1f}%</b></div>'
                                f'<div style="display:flex; justify-content:space-between; margin-bottom:7px;"><span>Effective Positions</span><b>{risk_engine["effective_positions"]:.1f}</b></div>'
                                f'<div style="display:flex; justify-content:space-between;"><span>Regime</span><b style="color:#2EE59D;">{regime_tag}</b></div>'
                            f'</div>'

                            f'<div style="display:grid; gap:8px;">'
                                f'<div style="padding:10px; border-radius:12px; background:{tail_color}18; border:1px solid {tail_color}44;">'
                                    f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.55);">Tail Fragility</div>'
                                    f'<div style="display:flex; justify-content:space-between; align-items:end; margin-top:4px;">'
                                        f'<span style="color:{tail_color}; font-weight:950;">{tail_label}</span>'
                                        f'<span style="color:{tail_color}; font-weight:950;">{tail_fragility_index:.0f}</span>'
                                    f'</div>'
                                f'</div>'
                                f'<div style="padding:10px; border-radius:12px; background:{liquidity_color}18; border:1px solid {liquidity_color}44;">'
                                    f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.55);">Liquidity Stress</div>'
                                    f'<div style="display:flex; justify-content:space-between; align-items:end; margin-top:4px;">'
                                        f'<span style="color:{liquidity_color}; font-weight:950;">{liquidity_label}</span>'
                                        f'<span style="color:{liquidity_color}; font-weight:950;">{liquidity_stress_score:.0f}</span>'
                                    f'</div>'
                                f'</div>'
                                f'<div style="padding:10px; border-radius:12px; background:{convexity_color}18; border:1px solid {convexity_color}44;">'
                                    f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.55);">Convexity</div>'
                                    f'<div style="display:flex; justify-content:space-between; align-items:end; margin-top:4px;">'
                                        f'<span style="color:{convexity_color}; font-weight:950;">{convexity_label}</span>'
                                        f'<span style="color:{convexity_color}; font-weight:950;">{convexity_score:.0f}</span>'
                                    f'</div>'
                                f'</div>'
                            f'</div>'

                        f'</div>'

                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:14px 0 12px 0;"></div>'

                        f'<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px;">'
                            f'<div style="padding:10px; border-radius:12px; background:{tail_color}14; border:1px solid {tail_color}44;">'
                                f'<div style="font-size:0.58rem; color:rgba(231,238,249,0.50); letter-spacing:0.07em;">TAIL PATH</div>'
                                f'<div style="font-size:0.9rem; font-weight:950; color:{tail_color}; margin-top:4px;">{tail_label}</div>'
                            f'</div>'
                            f'<div style="padding:10px; border-radius:12px; background:{liquidity_color}14; border:1px solid {liquidity_color}44;">'
                                f'<div style="font-size:0.58rem; color:rgba(231,238,249,0.50); letter-spacing:0.07em;">LIQUIDITY</div>'
                                f'<div style="font-size:0.9rem; font-weight:950; color:{liquidity_color}; margin-top:4px;">{liquidity_label}</div>'
                            f'</div>'
                            f'<div style="padding:10px; border-radius:12px; background:{convexity_color}14; border:1px solid {convexity_color}44;">'
                                f'<div style="font-size:0.58rem; color:rgba(231,238,249,0.50); letter-spacing:0.07em;">CONVEXITY</div>'
                                f'<div style="font-size:0.9rem; font-weight:950; color:{convexity_color}; margin-top:4px;">{convexity_label}</div>'
                            f'</div>'
                            f'<div style="padding:10px; border-radius:12px; background:rgba(58,141,255,0.10); border:1px solid rgba(58,141,255,0.35);">'
                                f'<div style="font-size:0.58rem; color:rgba(231,238,249,0.50); letter-spacing:0.07em;">REGIME PATH</div>'
                                f'<div style="font-size:0.9rem; font-weight:950; color:#73CFFF; margin-top:4px;">{regime_tag}</div>'
                            f'</div>'
                        f'</div>'

                        f'<div style="margin-top:11px; padding:10px; border-radius:12px; background:rgba(255,77,109,0.07); border:1px solid rgba(255,77,109,0.18);">'
                            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                                f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.55); letter-spacing:0.07em;">LIVE STRESS CONDITIONS</div>'
                                f'<div style="font-size:1.05rem; font-weight:950; color:#FF4D6D;">{overall_stress_impact:.1f}%</div>'
                            f'</div>'
                            f'<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; margin-top:8px; font-size:0.72rem;">'
                                f'<div><span style="color:rgba(231,238,249,0.55);">SPY -5%</span><br><b style="color:#FF4D6D;">{risk_engine["stress_market_down_5"]:.1f}%</b></div>'
                                f'<div><span style="color:rgba(231,238,249,0.55);">Regime</span><br><b style="color:#FF4D6D;">{regime_spy_down_5:.1f}%</b></div>'
                                f'<div><span style="color:rgba(231,238,249,0.55);">Liquidity</span><br><b style="color:{liquidity_color};">{liquidity_drag:.1f}%</b></div>'
                                f'<div><span style="color:rgba(231,238,249,0.55);">Convexity</span><br><b style="color:{convexity_color};">{convexity_drag:.1f}%</b></div>'
                            f'</div>'
                        f'</div>'

                    f'</div>'
                )
                st.markdown(risk_stack_html, unsafe_allow_html=True)
            # -----------------------------
            # Row 2: main operating panels
            # -----------------------------
            main_left, main_mid, main_right = st.columns([1.05, 0.95, 1.05], gap="medium")

            with main_left:
                st.markdown("### Exposure Concentration")

                exposure_rows_html = ""

                if not exposure_df.empty:
                    for _, row in exposure_df.iterrows():
                        ticker = row["Ticker"]
                        weight = row["Weight"]
                        vol = row["Volatility"]
                        corr_value = row["Correlation"]
                        risk_contrib = row["Risk Contribution %"]

                        risk_color = "#FF4D6D" if risk_contrib >= 12 else "#FFB020" if risk_contrib >= 6 else "#2EE59D"

                        exposure_rows_html += (
                            f'<div style="display:grid; grid-template-columns:0.7fr 0.7fr 0.8fr 0.8fr 1.1fr; gap:8px; '
                            f'align-items:center; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.055);">'
                                f'<div style="padding:3px 7px; border-radius:999px; background:{risk_color}20; '
                                f'border:1px solid {risk_color}55; color:{risk_color}; font-weight:950; font-size:0.72rem;">{ticker}</div>'
                                f'<div style="font-size:0.75rem;">{weight:.1f}%</div>'
                                f'<div style="font-size:0.75rem;">{vol:.1f}%</div>'
                                f'<div style="font-size:0.75rem; color:#73CFFF;">{corr_value:.2f}</div>'
                                f'<div>'
                                    f'<div style="display:flex; justify-content:space-between; font-size:0.75rem;">'
                                        f'<span style="color:{risk_color}; font-weight:950;">{risk_contrib:.1f}%</span>'
                                    f'</div>'
                                    f'<div style="height:5px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:3px; overflow:hidden;">'
                                        f'<div style="width:{min(risk_contrib,100):.1f}%; height:100%; background:{risk_color}; border-radius:999px;"></div>'
                                    f'</div>'
                                f'</div>'
                            f'</div>'
                        )

                exposure_html = (
                    f'<div class="portfolio-card" style="min-height:385px; padding:14px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900;">POSITION RISK STACK</div>'
                            f'<div style="font-size:0.72rem; color:#73CFFF; font-weight:900;">LIVE</div>'
                        f'</div>'
                        f'<div style="display:grid; grid-template-columns:0.7fr 0.7fr 0.8fr 0.8fr 1.1fr; gap:8px; '
                        f'font-size:0.62rem; color:rgba(231,238,249,0.45); font-weight:900; margin-bottom:5px;">'
                            f'<div>TICKER</div><div>WEIGHT</div><div>VOL</div><div>CORR</div><div>RISK CONTRIB.</div>'
                        f'</div>'
                        f'{exposure_rows_html}'
                        f'<div style="display:flex; gap:16px; margin-top:14px; font-size:0.72rem; color:rgba(231,238,249,0.65);">'
                            f'<span style="color:#FF4D6D;">● High &gt;12%</span>'
                            f'<span style="color:#FFB020;">● Elevated 6–12%</span>'
                            f'<span style="color:#2EE59D;">● Low &lt;6%</span>'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(exposure_html, unsafe_allow_html=True)

            with main_mid:
                st.markdown("### Stress Sensitivity")

                stress_items = [
                    ("SPY -2% Shock", risk_engine["stress_market_down_2"], "Beta shock", "#FFB020"),
                    ("SPY -5% Shock", risk_engine["stress_market_down_5"], "Market de-risk", "#FF4D6D"),
                    (regime_tag, regime_spy_down_5, "Regime-conditioned", "#FF4D6D"),
                    ("Liquidity Stress", liquidity_drag, "Exit-pressure proxy", liquidity_color),
                    ("Volatility Shock", -1 * (risk_engine["annual_vol"] / 100) * 30, "Vol expansion", "#FF4D6D"),
                    ("Convexity Drag", convexity_drag, "Nonlinear loss path", convexity_color),
                ]

                stress_rows_html = ""

                for label, value, tag, color in stress_items:
                    width = min(100, abs(value) * 8)

                    stress_rows_html += (
                        f'<div style="padding:9px 10px; margin-bottom:7px; border-radius:12px; '
                        f'background:linear-gradient(90deg, {color}2E, rgba(9,23,51,0.78)); '
                        f'border:1px solid {color}55;">'
                            f'<div style="display:flex; justify-content:space-between; align-items:flex-start;">'
                                f'<div>'
                                    f'<div style="font-size:0.78rem; font-weight:950; color:#E7EEF9;">{label}</div>'
                                    f'<div style="font-size:0.6rem; color:rgba(231,238,249,0.52); margin-top:1px;">{tag}</div>'
                                f'</div>'
                                f'<div style="font-size:0.98rem; font-weight:950; color:{color};">{value:.1f}%</div>'
                            f'</div>'
                            f'<div style="height:6px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:7px; overflow:hidden;">'
                                f'<div class="shock-bar" style="width:{width:.1f}%; height:100%; background:{color}; border-radius:999px; box-shadow:0 0 12px {color};"></div>'
                            f'</div>'
                        f'</div>'
                    )

                stress_html = (
                    f'<div class="portfolio-card" style="min-height:385px; padding:14px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:11px;">'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900;">STRESS LADDER</div>'
                            f'<div style="font-size:0.72rem; color:#FFB020; font-weight:900;">LIVE SHOCK MODEL</div>'
                        f'</div>'
                        f'{stress_rows_html}'
                        f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px;">'
                            f'<div style="padding:9px; border-radius:12px; background:{tail_color}18; border:1px solid {tail_color}44;">'
                                f'<div style="font-size:0.6rem; color:rgba(231,238,249,0.50); letter-spacing:0.07em;">TAIL PATH</div>'
                                f'<div style="font-size:0.8rem; font-weight:950; color:{tail_color}; margin-top:4px;">{tail_label}</div>'
                            f'</div>'
                            f'<div style="padding:9px; border-radius:12px; background:rgba(255,176,32,0.08); border:1px solid rgba(255,176,32,0.22);">'
                                f'<div style="font-size:0.6rem; color:rgba(231,238,249,0.50); letter-spacing:0.07em;">REGIME PATH</div>'
                                f'<div style="font-size:0.8rem; font-weight:950; color:#FFB020; margin-top:4px;">{regime_tag}</div>'
                            f'</div>'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(stress_html, unsafe_allow_html=True)

            with main_right:
                st.markdown("### AI Risk Commentary")

                risk_read = generate_risk_desk_brief(
                    risk_engine,
                    portfolio_type,
                    risk_level,
                    st.session_state.allocation_horizon
                )

                ai_risk_html = (
                    f'<div class="portfolio-card" style="min-height:385px; padding:18px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                            f'<div style="font-size:0.78rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em;">INTERNAL RISK DESK</div>'
                            f'<div style="font-size:0.72rem; color:#73CFFF; font-weight:900;">LIVE</div>'
                        f'</div>'
                        f'<div style="color:#E7EEF9; font-size:0.88rem; line-height:1.62;">'
                            f'{risk_read.replace(chr(10), "<br>")}'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(ai_risk_html, unsafe_allow_html=True)

            # -----------------------------
            # Row 3: bottom integrated diagnostics
            # -----------------------------
            add_left, add_mid, add_right = st.columns([1.05, 0.95, 1.05], gap="medium")

            with add_left:
                st.markdown("### Hidden Correlation Clusters")

                cluster_html = (
                    f'<div class="portfolio-card" style="min-height:225px; padding:14px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900;">CORRELATION STACK</div>'
                            f'<div style="font-size:0.72rem; color:#FFB020; font-weight:900;">CLUSTER SCAN</div>'
                        f'</div>'
                        f'{cluster_rows_html}'
                    f'</div>'
                )

                st.markdown(cluster_html, unsafe_allow_html=True)

            with add_mid:
                st.markdown("### Factor Decomposition")

                factor_html = (
                    f'<div class="portfolio-card" style="min-height:225px; padding:14px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900;">RISK FACTOR PROXY</div>'
                            f'<div style="font-size:0.72rem; color:#73CFFF; font-weight:900;">MODEL</div>'
                        f'</div>'
                        f'{factor_rows_html}'
                    f'</div>'
                )

                st.markdown(factor_html, unsafe_allow_html=True)

            with add_right:
                st.markdown("### Tail / Liquidity / Convexity")

                tlc_html = (
                    f'<div class="portfolio-card" style="min-height:225px; padding:14px;">'
                        f'<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px;">'
                            f'<div style="padding:12px; border-radius:14px; background:{tail_color}18; border:1px solid {tail_color}55; box-shadow:0 0 18px {tail_color}15;">'
                                f'<div style="font-size:0.62rem; color:rgba(231,238,249,0.52);">TAIL FRAGILITY</div>'
                                f'<div style="font-size:1.45rem; font-weight:950; color:{tail_color}; margin-top:5px;">{tail_fragility_index:.0f}</div>'
                                f'<div style="font-size:0.72rem; color:{tail_color};">{tail_label}</div>'
                            f'</div>'
                            f'<div style="padding:12px; border-radius:14px; background:{liquidity_color}18; border:1px solid {liquidity_color}55; box-shadow:0 0 18px {liquidity_color}15;">'
                                f'<div style="font-size:0.62rem; color:rgba(231,238,249,0.52);">LIQUIDITY</div>'
                                f'<div style="font-size:1.45rem; font-weight:950; color:{liquidity_color}; margin-top:5px;">{liquidity_stress_score:.0f}</div>'
                                f'<div style="font-size:0.72rem; color:{liquidity_color};">{liquidity_label}</div>'
                            f'</div>'
                            f'<div style="padding:12px; border-radius:14px; background:{convexity_color}18; border:1px solid {convexity_color}55; box-shadow:0 0 18px {convexity_color}15;">'
                                f'<div style="font-size:0.62rem; color:rgba(231,238,249,0.52);">CONVEXITY</div>'
                                f'<div style="font-size:1.45rem; font-weight:950; color:{convexity_color}; margin-top:5px;">{convexity_score:.0f}</div>'
                                f'<div style="font-size:0.72rem; color:{convexity_color};">{convexity_label}</div>'
                            f'</div>'
                        f'</div>'
                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:14px 0;"></div>'
                        f'<div style="color:rgba(231,238,249,0.68); font-size:0.78rem; line-height:1.5;">'
                            f'Composite institutional risk stack: tail loss pressure, exit-friction proxy, and nonlinear stress sensitivity.'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(tlc_html, unsafe_allow_html=True)

            st.markdown(
                f'<div class="portfolio-card" style="margin-top:10px; padding:10px 14px; display:flex; justify-content:center; gap:28px; '
                f'color:rgba(231,238,249,0.68); font-size:0.78rem;">'
                    f'<span style="color:#2EE59D; font-weight:950;">⚡ LIVE STRESS UPDATES</span>'
                    f'<span>Model refresh: Every 60s</span>'
                    f'<span>Regime: {regime_name}</span>'
                    f'<span>Shock mode: {regime_tag}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.stop()   

        if selected_view == "Stress Test Engine":
            st.markdown(
                """
                <style>
                @keyframes stressPulse {
                    0% { opacity:0.70; filter:brightness(0.95); }
                    50% { opacity:1; filter:brightness(1.20); }
                    100% { opacity:0.70; filter:brightness(0.95); }
                }
                .stress-live-bar {
                    animation: stressPulse 2.2s ease-in-out infinite;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # -----------------------------
            # Scenario presets
            # -----------------------------
            scenario_presets = {
                "2008 Crisis": {
                    "portfolio_shock": -32,
                    "spy_shock": -38,
                    "recovery_months": 24,
                    "failure": "equity beta + correlation compression",
                    "liquidity": "Severe",
                },
                "COVID Crash": {
                    "portfolio_shock": -24,
                    "spy_shock": -34,
                    "recovery_months": 9,
                    "failure": "volatility spike + liquidity gap",
                    "liquidity": "High",
                },
                "Inflation Shock": {
                    "portfolio_shock": -17,
                    "spy_shock": -20,
                    "recovery_months": 14,
                    "failure": "rates pressure + duration stress",
                    "liquidity": "Medium",
                },
                "Rate Shock": {
                    "portfolio_shock": -14,
                    "spy_shock": -12,
                    "recovery_months": 10,
                    "failure": "duration repricing",
                    "liquidity": "Medium",
                },
                "AI Bubble Unwind": {
                    "portfolio_shock": -28,
                    "spy_shock": -18,
                    "recovery_months": 18,
                    "failure": "growth crowding + high beta unwind",
                    "liquidity": "High",
                },
                "Liquidity Freeze": {
                    "portfolio_shock": -22,
                    "spy_shock": -16,
                    "recovery_months": 20,
                    "failure": "exit pressure + bid/ask widening",
                    "liquidity": "Severe",
                },
                "Custom Shock": {
                    "portfolio_shock": -20,
                    "spy_shock": -20,
                    "recovery_months": 12,
                    "failure": "custom stress path",
                    "liquidity": "Medium",
                },
            }

            st.markdown(
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<div>'
                            f'<div style="font-size:1.9rem; font-weight:950; color:#E7EEF9;">Stress Test Engine</div>'
                            f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">'
                                f'Crisis scenario analysis tied to the active {portfolio_type}.'
                            f'</div>'
                        f'</div>'
                        f'<div style="text-align:right;">'
                            f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.52);">CRISIS MODEL</div>'
                            f'<div style="font-size:1rem; color:#2EE59D; font-weight:900;">LIVE</div>'
                        f'</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            control_cols = st.columns([1.4, 1, 1, 1, 1], gap="medium")

            with control_cols[0]:
                selected_shock = st.selectbox(
                    "Shock Scenario",
                    list(scenario_presets.keys()),
                    index=0,
                    key="stress_selected_shock"
                )

            with control_cols[1]:
                custom_portfolio_shock = st.slider(
                    "Custom Portfolio Shock",
                    -60,
                    0,
                    scenario_presets[selected_shock]["portfolio_shock"],
                    key="stress_custom_portfolio_shock"
                )

            with control_cols[2]:
                custom_spy_shock = st.slider(
                    "Custom SPY Shock",
                    -60,
                    0,
                    scenario_presets[selected_shock]["spy_shock"],
                    key="stress_custom_spy_shock"
                )

            with control_cols[3]:
                recovery_months = st.slider(
                    "Recovery Months",
                    3,
                    36,
                    scenario_presets[selected_shock]["recovery_months"],
                    key="stress_recovery_months"
                )

            with control_cols[4]:
                liquidity_mode = st.selectbox(
                    "Liquidity Mode",
                    ["Normal", "Medium", "High", "Severe"],
                    index=["Normal", "Medium", "High", "Severe"].index(scenario_presets[selected_shock]["liquidity"]),
                    key="stress_liquidity_mode"
                )

            portfolio_shock = custom_portfolio_shock
            spy_shock = custom_spy_shock
            drawdown_gap = portfolio_shock - spy_shock
            stressed_value = portfolio_size * (1 + portfolio_shock / 100)
            dollar_loss = portfolio_size - stressed_value
            capital_at_risk = max(0, dollar_loss)

            recovery_estimate = f"{recovery_months} mo"
            failure_path = scenario_presets[selected_shock]["failure"]

            severity_label = "Critical" if portfolio_shock <= -30 else "High" if portfolio_shock <= -20 else "Moderate"
            severity_color = "#FF4D6D" if portfolio_shock <= -30 else "#FFB020" if portfolio_shock <= -20 else "#2EE59D"

            hedge_effectiveness = "Strong" if selected_shock in ["Inflation Shock", "Rate Shock"] else "Partial" if selected_shock in ["2008 Crisis", "COVID Crash"] else "Weak"
            hedge_color = "#2EE59D" if hedge_effectiveness == "Strong" else "#FFB020" if hedge_effectiveness == "Partial" else "#FF4D6D"

            liquidity_color = "#FF4D6D" if liquidity_mode == "Severe" else "#FFB020" if liquidity_mode in ["High", "Medium"] else "#2EE59D"

            metric_cards = [
                ("Portfolio Impact", f"{portfolio_shock:.1f}%", severity_color),
                ("Dollar Loss", f"${dollar_loss:,.0f}", "#FF4D6D"),
                ("Stressed Value", f"${stressed_value:,.0f}", "#E7EEF9"),
                ("SPY Impact", f"{spy_shock:.1f}%", "#FF4D6D"),
                ("Drawdown Gap", f"{drawdown_gap:+.1f}%", "#FFB020"),
                ("Recovery Estimate", recovery_estimate, "#73CFFF"),
                ("Liquidity Stress", liquidity_mode, liquidity_color),
                ("Hedge Effectiveness", hedge_effectiveness, hedge_color),
            ]

            metric_html = (
                f'<div style="display:grid; grid-template-columns:repeat(8, minmax(0, 1fr)); gap:10px; margin-top:14px;">'
            )

            for label, value, color in metric_cards:
                metric_html += (
                    f'<div class="metric-tile">'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-value" style="color:{color};">{value}</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:10px; overflow:hidden;">'
                            f'<div class="stress-live-bar" style="width:78%; height:100%; background:{color}; border-radius:999px; opacity:0.72;"></div>'
                        f'</div>'
                    f'</div>'
                )

            metric_html += f'</div>'
            st.markdown(metric_html, unsafe_allow_html=True)

            # -----------------------------
            # Holding damage logic
            # -----------------------------
            stress_tickers = [p["ticker"] for p in recommendations if p["ticker"] != "CASH"]
            stress_weights = [
                p["dollars"] / sum(x["dollars"] for x in recommendations if x["ticker"] != "CASH")
                for p in recommendations
                if p["ticker"] != "CASH"
            ]

            damage_rows = []

            for ticker, weight in zip(stress_tickers, stress_weights):
                if ticker in ["TLT", "SHY", "IEF"]:
                    shock_mult = 0.25 if selected_shock in ["2008 Crisis", "COVID Crash"] else 0.75
                    reason = "duration hedge / rates sensitivity"
                elif ticker in ["GLD", "IAU"]:
                    shock_mult = 0.15
                    reason = "defensive hedge sleeve"
                elif ticker in ["NVDA", "TSLA", "MSTR", "SMH", "QQQ"]:
                    shock_mult = 1.35
                    reason = "growth beta / convexity pressure"
                elif ticker in ["SPY", "VTI"]:
                    shock_mult = 1.00
                    reason = "broad market beta"
                else:
                    shock_mult = 0.95
                    reason = "equity beta exposure"

                ticker_shock = portfolio_shock * shock_mult
                ticker_dollar_loss = portfolio_size * weight * abs(ticker_shock / 100)
                contribution = ticker_dollar_loss / max(1, dollar_loss) * 100

                row_color = "#FF4D6D" if ticker_shock <= -30 else "#FFB020" if ticker_shock <= -15 else "#2EE59D"

                damage_rows.append(
                    {
                        "ticker": ticker,
                        "weight": weight,
                        "shock": ticker_shock,
                        "dollar_loss": ticker_dollar_loss,
                        "contribution": contribution,
                        "reason": reason,
                        "color": row_color,
                    }
                )

            damage_rows = sorted(damage_rows, key=lambda x: x["dollar_loss"], reverse=True)

            largest_loss_driver = damage_rows[0]["ticker"] if damage_rows else "N/A"
            first_failure_point = failure_path
            correlation_failure = "Likely" if selected_shock in ["2008 Crisis", "COVID Crash", "AI Bubble Unwind", "Liquidity Freeze"] else "Moderate"

            # -----------------------------
            # Shock path chart
            # -----------------------------
            path_days = list(range(0, 253))
            shock_day = 30
            plateau_end = 75

            shock_values = []

            for day in path_days:
                if day <= shock_day:
                    value = portfolio_size + (stressed_value - portfolio_size) * (day / shock_day)
                elif day <= plateau_end:
                    value = stressed_value * (1 + 0.015 * ((day - shock_day) / (plateau_end - shock_day)))
                else:
                    recovery_progress = (day - plateau_end) / (252 - plateau_end)
                    recovered_value = stressed_value + (portfolio_size - stressed_value) * min(1, recovery_progress * (12 / max(3, recovery_months)))
                    value = recovered_value

                shock_values.append(value)

            main_left, main_right = st.columns([2.1, 1], gap="medium")

            with main_left:
                st.markdown("### Shock Path")

                fig_shock = go.Figure()

                fig_shock.add_trace(
                    go.Scatter(
                        x=path_days,
                        y=shock_values,
                        mode="lines",
                        name="Stress Path",
                        line=dict(color="#FF4D6D", width=4),
                        fill="tozeroy",
                        fillcolor="rgba(255,77,109,0.08)",
                    )
                )

                fig_shock.add_hline(
                    y=portfolio_size,
                    line_dash="dash",
                    line_color="rgba(231,238,249,0.45)",
                    annotation_text="Base Value",
                    annotation_position="right",
                )

                fig_shock.add_hline(
                    y=stressed_value,
                    line_dash="dot",
                    line_color="#FF4D6D",
                    annotation_text="Shock Low",
                    annotation_position="right",
                )

                fig_shock.add_trace(
                    go.Scatter(
                        x=[shock_day],
                        y=[stressed_value],
                        mode="markers+text",
                        marker=dict(size=11, color="#FF4D6D"),
                        text=[f"${stressed_value:,.0f}"],
                        textposition="bottom right",
                        textfont=dict(color="#FF4D6D", size=12),
                        showlegend=False,
                    )
                )

                fig_shock.update_layout(
                    height=520,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(3,8,20,0.58)",
                    font=dict(color="#E7EEF9"),
                    margin=dict(l=10, r=20, t=10, b=10),
                    hovermode="x unified",
                    legend=dict(
                        orientation="h",
                        y=1.05,
                        x=0,
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    xaxis=dict(
                        title="Stress Days",
                        gridcolor="rgba(255,255,255,0.055)",
                        zeroline=False,
                    ),
                    yaxis=dict(
                        title="Portfolio Value",
                        gridcolor="rgba(255,255,255,0.06)",
                        zeroline=False,
                    ),
                )

                st.plotly_chart(fig_shock, use_container_width=True)

            with main_right:
                st.markdown("### Portfolio Breakpoint")

                breakpoint_html = (
                    f'<div class="portfolio-card" style="min-height:520px; padding:16px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'BREAKPOINT MAP'
                        f'</div>'

                        f'<div style="padding:12px; border-radius:14px; background:rgba(255,77,109,0.10); border:1px solid rgba(255,77,109,0.35); margin-bottom:12px;">'
                            f'<div style="font-size:0.65rem; color:rgba(231,238,249,0.52);">FIRST FAILURE POINT</div>'
                            f'<div style="font-size:0.95rem; color:#FF4D6D; font-weight:950; margin-top:5px;">{first_failure_point}</div>'
                        f'</div>'

                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Largest Loss Driver</span><b style="color:#FF4D6D;">{largest_loss_driver}</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Correlation Failure</span><b style="color:#FFB020;">{correlation_failure}</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Liquidity Stress</span><b style="color:{liquidity_color};">{liquidity_mode}</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Hedge Effectiveness</span><b style="color:{hedge_color};">{hedge_effectiveness}</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Capital at Risk</span><b style="color:#FF4D6D;">${capital_at_risk:,.0f}</b></div>'

                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:16px 0;"></div>'

                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:12px;">'
                            f'DEFENSE SLEEVE EFFECTIVENESS'
                        f'</div>'

                        f'<div style="display:grid; gap:9px;">'
                            f'<div style="display:flex; justify-content:space-between;"><span>TLT / Duration</span><b style="color:#73CFFF;">{"Helpful" if selected_shock in ["2008 Crisis", "COVID Crash"] else "Mixed"}</b></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>GLD / Gold</span><b style="color:#2EE59D;">Helpful</b></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>SHY / Cash-like</span><b style="color:#2EE59D;">Stabilizer</b></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Growth Sleeve</span><b style="color:#FF4D6D;">Primary Damage</b></div>'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(breakpoint_html, unsafe_allow_html=True)

         # -----------------------------
            # Institutional Deep Dive Row
            # -----------------------------
            deep_left, deep_mid, deep_right = st.columns([1.05, 1.05, 1.25], gap="medium")

            with deep_left:
                st.markdown("### Scenario Assumptions")

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:300px; padding:16px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">STRESS INPUTS</div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Scenario</span><b style="color:#E7EEF9;">{selected_shock}</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Portfolio Shock</span><b style="color:#FF4D6D;">{portfolio_shock:.1f}%</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>SPY Shock</span><b style="color:#FF4D6D;">{spy_shock:.1f}%</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Recovery Window</span><b style="color:#73CFFF;">{recovery_months} mo</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Liquidity Mode</span><b style="color:{liquidity_color};">{liquidity_mode}</b></div>'
                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:15px 0;"></div>'
                        f'<div style="color:rgba(231,238,249,0.68); font-size:0.82rem; line-height:1.55;">'
                            f'Scenario applies a forced drawdown path, liquidity penalty, and recovery slope against the active allocation.'
                        f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with deep_mid:
                st.markdown("### Defense Sleeve Effectiveness")

                defense_rows = [
                    ("TLT / Duration", "Helpful" if selected_shock in ["2008 Crisis", "COVID Crash"] else "Mixed", "#73CFFF"),
                    ("GLD / Gold", "Helpful", "#2EE59D"),
                    ("SHY / Cash-like", "Stabilizer", "#2EE59D"),
                    ("Growth Sleeve", "Primary Damage", "#FF4D6D"),
                    ("Core Beta", "Systemic Hit", "#FFB020"),
                ]

                defense_html = (
                    f'<div class="portfolio-card" style="min-height:300px; padding:16px;">'
                    f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">HEDGE RESPONSE</div>'
                )

                for label, value, color in defense_rows:
                    defense_html += (
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:12px;">'
                            f'<span>{label}</span>'
                            f'<b style="color:{color};">{value}</b>'
                        f'</div>'
                    )

                defense_html += f'</div>'

                st.markdown(defense_html, unsafe_allow_html=True)

            with deep_right:
                st.markdown("### AI Crisis Interpretation")

                crisis_read = (
                    f"[Primary Failure Path]<br>"
                    f"Cross-asset correlation compression drives the majority of downside transmission. "
                    f"{largest_loss_driver} becomes the dominant drag vector as beta dispersion collapses under {selected_shock}.<br><br>"

                    f"[Liquidity Regime]<br>"
                    f"Liquidity conditions deteriorate materially during the stress window. "
                    f"Defensive rotation remains partially effective, though execution quality weakens as volatility expands and market depth thins.<br><br>"

                    f"[Portfolio Fragility]<br>"
                    f"Portfolio drawdown reaches <b style='color:#FF4D6D;'>${dollar_loss:,.0f}</b>, "
                    f"with stressed NAV declining to <b>${stressed_value:,.0f}</b>. "
                    f"Relative drawdown spread versus SPY widens to "
                    f"<b style='color:#FFB020;'>{drawdown_gap:+.1f}%</b>, indicating elevated systematic exposure.<br><br>"

                    f"[Hedge Efficiency]<br>"
                    f"Duration and gold sleeves absorb portions of systemic pressure, while growth concentration remains the primary volatility amplifier. "
                    f"Hedge stack effectiveness currently registers as "
                    f"<b style='color:{hedge_color};'>{hedge_effectiveness}</b>.<br><br>"

                    f"[AI Risk Directive]<br>"
                    f"Reduce crowded beta exposure, prioritize liquidity preservation, and avoid leverage expansion until volatility normalization confirms regime stabilization."
                )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:300px; padding:16px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                            f'<div style="font-size:0.78rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em;">CRISIS DESK READ</div>'
                            f'<div style="font-size:0.72rem; color:#FF4D6D; font-weight:900;">LIVE STRESS</div>'
                        f'</div>'
                        f'<div style="color:#E7EEF9; font-size:0.88rem; line-height:1.62;">{crisis_read}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.stop()

        if selected_view == "Factor Engine":
            factor_tickers = [p["ticker"] for p in recommendations if p["ticker"] != "CASH"]
            factor_total = sum(p["dollars"] for p in recommendations if p["ticker"] != "CASH")

            factor_weights = {
                p["ticker"]: p["dollars"] / factor_total
                for p in recommendations
                if p["ticker"] != "CASH"
            }

            factor_map = {
                "Market Beta": ["SPY", "VTI", "QQQ"],
                "Growth": ["QQQ", "NVDA", "MSFT", "AMZN", "SMH", "TSLA"],
                "Quality": ["MSFT", "AAPL", "GOOGL"],
                "Momentum": ["NVDA", "SMH", "MSTR", "TSLA"],
                "Duration": ["TLT", "IEF"],
                "Defensive": ["GLD", "SHY", "TLT"],
                "High Beta / Convexity": ["MSTR", "TSLA", "NVDA", "SMH"],
            }

            factor_scores = {}

            for factor, names in factor_map.items():
                score = 0
                for ticker, weight in factor_weights.items():
                    if ticker in names:
                        score += weight * 100
                factor_scores[factor] = min(100, score)

            market_beta_score = min(100, max(0, float(live_perf["sharpe"]) * 35 if live_perf else 50))
            factor_scores["Market Beta"] = max(factor_scores.get("Market Beta", 0), market_beta_score)

            growth_score = factor_scores.get("Growth", 0)
            defensive_score = factor_scores.get("Defensive", 0)
            high_beta_score = factor_scores.get("High Beta / Convexity", 0)
            duration_score = factor_scores.get("Duration", 0)

            crowding_score = min(100, growth_score * 0.7 + high_beta_score * 0.9)
            balance_score = min(100, defensive_score * 1.2 + duration_score * 0.8)
            style_drift = max(0, crowding_score - balance_score)

            dominant_factor = max(factor_scores, key=factor_scores.get)
            dominant_factor_value = factor_scores[dominant_factor]

            factor_risk_label = "Crowded Growth" if crowding_score >= 55 else "Balanced Factor Mix" if balance_score >= 25 else "Beta-Led"
            factor_risk_color = "#FF4D6D" if crowding_score >= 65 else "#FFB020" if crowding_score >= 40 else "#2EE59D"

            factor_health = 100
            factor_health -= min(35, crowding_score * 0.35)
            factor_health -= min(25, style_drift * 0.30)
            factor_health += min(20, balance_score * 0.25)
            factor_health = max(0, min(100, factor_health))

            factor_health_label = "Strong" if factor_health >= 75 else "Watch" if factor_health >= 55 else "Crowded"
            factor_health_color = "#2EE59D" if factor_health >= 75 else "#FFB020" if factor_health >= 55 else "#FF4D6D"

            st.markdown(
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<div>'
                            f'<div style="font-size:1.75rem; font-weight:950; color:#E7EEF9;">Factor Engine</div>'
                            f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">'
                                f'Institutional factor exposure, crowding, and style-drift analysis tied to the active allocation.'
                            f'</div>'
                        f'</div>'
                        f'<div style="text-align:right;">'
                            f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.52);">FACTOR MODEL</div>'
                            f'<div style="font-size:1rem; color:#2EE59D; font-weight:900;">LIVE</div>'
                        f'</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            factor_metric_cards = [
                ("Dominant Factor", dominant_factor, "#73CFFF"),
                ("Dominant Load", f"{dominant_factor_value:.0f}/100", "#73CFFF"),
                ("Growth Load", f"{growth_score:.0f}/100", "#2EE59D"),
                ("High Beta", f"{high_beta_score:.0f}/100", "#FF4D6D"),
                ("Defense Load", f"{defensive_score:.0f}/100", "#FFB020"),
                ("Crowding", f"{crowding_score:.0f}/100", factor_risk_color),
                ("Style Drift", f"{style_drift:.0f}/100", "#FFB020"),
                ("Factor Health", f"{factor_health:.0f}/100", factor_health_color),
            ]

            metric_html = (
                f'<div style="display:grid; grid-template-columns:repeat(8, minmax(0, 1fr)); '
                f'gap:10px; margin-top:14px; margin-bottom:14px;">'
            )

            for label, value, color in factor_metric_cards:
                metric_html += (
                    f'<div class="metric-tile" style="min-height:105px; padding:14px;">'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-value" style="color:{color}; font-size:1.25rem;">{value}</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:12px; overflow:hidden;">'
                            f'<div style="width:78%; height:100%; background:{color}; border-radius:999px;"></div>'
                        f'</div>'
                    f'</div>'
                )

            metric_html += f'</div>'

            st.markdown(metric_html, unsafe_allow_html=True)

            factor_left, factor_mid, factor_right = st.columns([1.15, 1.25, 1.05], gap="medium")

            with factor_left:
                st.markdown("### Factor Loadings")

                factor_rows = ""

                for factor, score in sorted(factor_scores.items(), key=lambda x: x[1], reverse=True):
                    color = "#FF4D6D" if score >= 55 else "#FFB020" if score >= 30 else "#2EE59D"

                    factor_rows += (
                        f'<div style="margin-bottom:13px;">'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                                f'<span style="color:#E7EEF9;">{factor}</span>'
                                f'<span style="color:{color}; font-weight:950;">{score:.0f}</span>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                                f'<div style="width:{score:.1f}%; height:100%; background:{color}; border-radius:999px;"></div>'
                            f'</div>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:430px; padding:16px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'LIVE FACTOR STACK'
                        f'</div>'
                        f'{factor_rows}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with factor_mid:
                st.markdown("### Factor Exposure Map")

                fig_factor = go.Figure()

                fig_factor.add_trace(
                    go.Bar(
                        x=list(factor_scores.keys()),
                        y=list(factor_scores.values()),
                        marker=dict(
                            color=[
                                "#FF4D6D" if v >= 55 else "#FFB020" if v >= 30 else "#2EE59D"
                                for v in factor_scores.values()
                            ]
                        ),
                    )
                )

                fig_factor.update_layout(
                    height=430,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(3,8,20,0.58)",
                    font=dict(color="#E7EEF9"),
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.055)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", range=[0, 100]),
                    showlegend=False,
                )

                st.plotly_chart(fig_factor, use_container_width=True)

            with factor_right:
                st.markdown("### Factor Crowding")

                crowd_html = (
                    f'<div class="portfolio-card" style="min-height:430px; padding:16px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'CROWDING / STYLE DRIFT'
                        f'</div>'

                        f'<div style="padding:14px; border-radius:14px; background:{factor_risk_color}18; border:1px solid {factor_risk_color}55; margin-bottom:12px;">'
                            f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.55);">FACTOR POSTURE</div>'
                            f'<div style="font-size:1.25rem; font-weight:950; color:{factor_risk_color}; margin-top:5px;">{factor_risk_label}</div>'
                        f'</div>'

                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;"><span>Growth Crowding</span><b style="color:#FF4D6D;">{crowding_score:.0f}/100</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;"><span>Defense Balance</span><b style="color:#2EE59D;">{balance_score:.0f}/100</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;"><span>Style Drift</span><b style="color:#FFB020;">{style_drift:.0f}/100</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;"><span>Factor Health</span><b style="color:{factor_health_color};">{factor_health_label}</b></div>'

                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:15px 0;"></div>'

                        f'<div style="color:rgba(231,238,249,0.68); font-size:0.82rem; line-height:1.55;">'
                            f'Engine detects whether the allocation is dominated by beta, growth, duration, defensive ballast, or high-convexity exposure.'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(crowd_html, unsafe_allow_html=True)

            bottom_left, bottom_mid, bottom_right = st.columns([1.05, 1.05, 1.25], gap="medium")

            with bottom_left:
                st.markdown("### Holding Factor Attribution")

                holding_rows = ""

                for ticker, weight in sorted(factor_weights.items(), key=lambda x: x[1], reverse=True):
                    tags = []

                    if ticker in factor_map["Growth"]:
                        tags.append("Growth")
                    if ticker in factor_map["High Beta / Convexity"]:
                        tags.append("High Beta")
                    if ticker in factor_map["Defensive"]:
                        tags.append("Defense")
                    if ticker in factor_map["Duration"]:
                        tags.append("Duration")
                    if ticker in factor_map["Market Beta"]:
                        tags.append("Beta")

                    tag_text = " / ".join(tags) if tags else "Idiosyncratic"
                    severity = weight * 100
                    color = "#FF4D6D" if severity >= 15 else "#FFB020" if severity >= 7 else "#2EE59D"

                    holding_rows += (
                        f'<div style="display:grid; grid-template-columns:0.7fr 0.6fr 1.4fr; gap:8px; '
                        f'padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.06); align-items:center;">'
                            f'<div style="padding:4px 8px; border-radius:999px; background:{color}20; border:1px solid {color}55; color:{color}; font-weight:950; font-size:0.72rem;">{ticker}</div>'
                            f'<div style="font-size:0.78rem; font-weight:850;">{weight:.1%}</div>'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.70);">{tag_text}</div>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:315px; padding:14px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:10px;">'
                            f'HOLDING ATTRIBUTION'
                        f'</div>'
                        f'{holding_rows}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with bottom_mid:
                st.markdown("### Regime Sensitivity")

                regime_rows = [
                    ("Risk-On", "Positive", growth_score, "#2EE59D"),
                    ("Rates Up", "Pressure", duration_score, "#FFB020"),
                    ("Growth Unwind", "Exposed", growth_score + high_beta_score, "#FF4D6D"),
                    ("Defensive Rotation", "Buffered", defensive_score, "#73CFFF"),
                    ("Liquidity Shock", "Watch", high_beta_score, "#FFB020"),
                ]

                regime_html = (
                    f'<div class="portfolio-card" style="min-height:315px; padding:14px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:12px;">'
                            f'FACTOR REGIME MAP'
                        f'</div>'
                )

                for name, status, score, color in regime_rows:
                    regime_html += (
                        f'<div style="margin-bottom:12px;">'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                                f'<span>{name}</span>'
                                f'<span style="color:{color}; font-weight:950;">{status}</span>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                                f'<div style="width:{min(100, score):.1f}%; height:100%; background:{color}; border-radius:999px;"></div>'
                            f'</div>'
                        f'</div>'
                    )

                regime_html += f'</div>'

                st.markdown(regime_html, unsafe_allow_html=True)

            with bottom_right:
                st.markdown("### AI Factor Interpretation")

                factor_read = (
                    f"[Factor Desk Read]<br>"
                    f"Book is currently dominated by <b style='color:#73CFFF;'>{dominant_factor}</b> exposure. "
                    f"Primary factor load registers at <b>{dominant_factor_value:.0f}/100</b>, with crowding score at "
                    f"<b style='color:{factor_risk_color};'>{crowding_score:.0f}/100</b>.<br><br>"

                    f"[Crowding Risk]<br>"
                    f"Growth and high-beta sleeves create the main style concentration. "
                    f"Factor drift is <b style='color:#FFB020;'>{style_drift:.0f}/100</b>, meaning the book may behave less diversified than headline allocation implies.<br><br>"

                    f"[Defense Read]<br>"
                    f"Defensive ballast scores <b style='color:#2EE59D;'>{balance_score:.0f}/100</b>. "
                    f"Duration, gold, and cash-like sleeves provide partial offset but do not fully neutralize beta compression.<br><br>"

                    f"[AI Factor Directive]<br>"
                    f"Keep growth exposure if regime stays risk-on; trim high-beta crowding if dispersion breaks."
                )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:315px; padding:16px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                            f'<div style="font-size:0.78rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em;">AI FACTOR INTERPRETATION</div>'
                            f'<div style="font-size:0.72rem; color:#2EE59D; font-weight:900;">LIVE FACTOR READ</div>'
                        f'</div>'
                        f'<div style="color:#E7EEF9; font-size:0.88rem; line-height:1.62;">{factor_read}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown(
                f'<div class="portfolio-card" style="margin-top:10px; padding:10px 14px; display:flex; justify-content:center; gap:28px; '
                f'color:rgba(231,238,249,0.68); font-size:0.78rem;">'
                    f'<span style="color:#2EE59D; font-weight:950;">FACTOR MODEL LIVE</span>'
                    f'<span>Dominant: {dominant_factor}</span>'
                    f'<span>Crowding: {crowding_score:.0f}/100</span>'
                    f'<span>Style Drift: {style_drift:.0f}/100</span>'
                    f'<span>Health: {factor_health_label}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.stop()

        if selected_view == "Correlation Engine":
            corr = calculate_allocation_correlation_matrix(
                recommendations,
                st.session_state.allocation_horizon
            )

            st.markdown(
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<div>'
                            f'<div style="font-size:1.75rem; font-weight:950; color:#E7EEF9;">Correlation Engine</div>'
                            f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">'
                                f'Institutional correlation clustering, hidden concentration, and diversification integrity analysis.'
                            f'</div>'
                        f'</div>'
                        f'<div style="text-align:right;">'
                            f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.52);">CORRELATION MODEL</div>'
                            f'<div style="font-size:1rem; color:#2EE59D; font-weight:900;">LIVE</div>'
                        f'</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            if corr is None:
                st.warning("Correlation Engine data unavailable. Try again once market data loads.")
                st.stop()

            corr_pairs = []

            for i, t1 in enumerate(corr.columns):
                for t2 in corr.columns[i + 1:]:
                    c = float(corr.loc[t1, t2])
                    corr_pairs.append((t1, t2, c))

            corr_pairs = sorted(corr_pairs, key=lambda x: abs(x[2]), reverse=True)

            high_corr_pairs = [p for p in corr_pairs if p[2] >= 0.75]
            inverse_pairs = [p for p in corr_pairs if p[2] <= -0.25]

            avg_corr = np.mean([p[2] for p in corr_pairs]) if corr_pairs else 0
            max_corr = max([p[2] for p in corr_pairs]) if corr_pairs else 0
            cluster_count = len(high_corr_pairs)
            hedge_pairs = len(inverse_pairs)

            concentration_score = min(
                100,
                (avg_corr * 55) +
                (max_corr * 20) +
                (cluster_count * 3)
            )

            diversification_score = max(
                0,
                min(
                    100,
                    85
                    - concentration_score
                    + (hedge_pairs * 6)
                    + (defensive_score * 0.25 if "defensive_score" in locals() else 0)
                )
            )

            corr_state = "Compressed" if concentration_score >= 65 else "Clustered" if concentration_score >= 40 else "Diversified"
            corr_color = "#FF4D6D" if concentration_score >= 65 else "#FFB020" if concentration_score >= 40 else "#2EE59D"

            metric_cards = [
                ("Average Corr.", f"{avg_corr:.2f}", "#E7EEF9"),
                ("Max Pair Corr.", f"{max_corr:.2f}", "#FF4D6D" if max_corr >= 0.75 else "#2EE59D"),
                ("High-Corr Pairs", f"{cluster_count}", "#FFB020"),
                ("Hedge Pairs", f"{hedge_pairs}", "#73CFFF"),
                ("Concentration", f"{concentration_score:.0f}/100", corr_color),
                ("Diversification", f"{diversification_score:.0f}/100", "#2EE59D" if diversification_score >= 65 else "#FFB020"),
                ("Correlation State", corr_state, corr_color),
            ]

            metric_html = (
                f'<div style="display:grid; grid-template-columns:repeat(7, minmax(0, 1fr)); '
                f'gap:10px; margin-top:14px; margin-bottom:14px;">'
            )

            for label, value, color in metric_cards:
                metric_html += (
                    f'<div class="metric-tile" style="min-height:105px; padding:14px;">'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-value" style="color:{color}; font-size:1.25rem;">{value}</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:12px; overflow:hidden;">'
                            f'<div style="width:78%; height:100%; background:{color}; border-radius:999px;"></div>'
                        f'</div>'
                    f'</div>'
                )

            metric_html += f'</div>'
            st.markdown(metric_html, unsafe_allow_html=True)

            left_col, mid_col, right_col = st.columns([1.15, 1.25, 1.05], gap="medium")

            with left_col:
                st.markdown("### Correlation Heatmap")

                fig_corr = go.Figure(
                    data=go.Heatmap(
                        z=corr.values,
                        x=corr.columns,
                        y=corr.index,
                        colorscale=[
                            [0, "#FF4D6D"],
                            [0.5, "#091733"],
                            [1, "#2EE59D"],
                        ],
                        zmin=-1,
                        zmax=1,
                        colorbar=dict(title="Corr"),
                    )
                )

                fig_corr.update_layout(
                    height=480,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(3,8,20,0.58)",
                    font=dict(color="#E7EEF9"),
                    margin=dict(l=10, r=10, t=10, b=10),
                )

                st.plotly_chart(fig_corr, use_container_width=True)

            with mid_col:
                st.markdown("### Hidden Cluster Stack")

                cluster_rows = ""

                for t1, t2, c in corr_pairs[:8]:
                    color = "#FF4D6D" if c >= 0.85 else "#FFB020" if c >= 0.65 else "#2EE59D"
                    label = "Compression" if c >= 0.85 else "Cluster" if c >= 0.65 else "Loose"

                    cluster_rows += (
                        f'<div style="margin-bottom:12px;">'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                                f'<span style="color:#E7EEF9;">{t1} / {t2}</span>'
                                f'<span style="color:{color}; font-weight:950;">{c:.2f}</span>'
                            f'</div>'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.68rem; color:rgba(231,238,249,0.55); margin-top:2px;">'
                                f'<span>{label}</span><span>pair risk</span>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                                f'<div style="width:{abs(c) * 100:.1f}%; height:100%; background:{color}; border-radius:999px;"></div>'
                            f'</div>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:480px; padding:16px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'PAIRWISE CORRELATION STACK'
                        f'</div>'
                        f'{cluster_rows}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with right_col:
                st.markdown("### Diversification Integrity")

                integrity_html = (
                    f'<div class="portfolio-card" style="min-height:480px; padding:16px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'DIVERSIFICATION CHECK'
                        f'</div>'

                        f'<div style="padding:14px; border-radius:14px; background:{corr_color}18; border:1px solid {corr_color}55; margin-bottom:14px;">'
                            f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.55);">CORRELATION POSTURE</div>'
                            f'<div style="font-size:1.25rem; font-weight:950; color:{corr_color}; margin-top:5px;">{corr_state}</div>'
                        f'</div>'

                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;"><span>Avg Pair Correlation</span><b>{avg_corr:.2f}</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;"><span>Cluster Count</span><b style="color:#FFB020;">{cluster_count}</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;"><span>Hedge Pairs</span><b style="color:#73CFFF;">{hedge_pairs}</b></div>'
                        f'<div style="display:flex; justify-content:space-between; margin-bottom:11px;"><span>Diversification Score</span><b style="color:#2EE59D;">{diversification_score:.0f}/100</b></div>'

                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:15px 0;"></div>'

                        f'<div style="color:rgba(231,238,249,0.68); font-size:0.82rem; line-height:1.55;">'
                            f'Engine checks whether positions are genuinely diversifying the allocation or collapsing into the same risk trade under stress.'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(integrity_html, unsafe_allow_html=True)

            bottom_left, bottom_mid, bottom_right = st.columns([1.05, 1.05, 1.25], gap="medium")

            with bottom_left:
                st.markdown("### Correlation Regime Map")

                regime_rows = [
                    ("Risk-On", "Stable", avg_corr * 100, "#2EE59D"),
                    ("Vol Shock", "Compresses", concentration_score, "#FF4D6D"),
                    ("Liquidity Stress", "Pairs Tighten", concentration_score * 0.9, "#FFB020"),
                    ("Growth Unwind", "Cluster Risk", cluster_count * 15, "#FF4D6D"),
                    ("Defensive Bid", "Hedges Engage", hedge_pairs * 25, "#73CFFF"),
                ]

                regime_html = (
                    f'<div class="portfolio-card" style="min-height:315px; padding:14px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:12px;">'
                            f'CORRELATION REGIME MAP'
                        f'</div>'
                )

                for name, status, score, color in regime_rows:
                    regime_html += (
                        f'<div style="margin-bottom:12px;">'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                                f'<span>{name}</span>'
                                f'<span style="color:{color}; font-weight:950;">{status}</span>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                                f'<div style="width:{min(100, max(4, abs(score))):.1f}%; height:100%; background:{color}; border-radius:999px;"></div>'
                            f'</div>'
                        f'</div>'
                    )

                regime_html += f'</div>'

                st.markdown(regime_html, unsafe_allow_html=True)

            with bottom_mid:
                st.markdown("### Pair Failure Watchlist")

                watch_rows = ""

                for t1, t2, c in corr_pairs[:6]:
                    color = "#FF4D6D" if c >= 0.85 else "#FFB020" if c >= 0.65 else "#2EE59D"

                    watch_rows += (
                        f'<div style="display:grid; grid-template-columns:1.1fr 0.5fr 1fr; gap:8px; '
                        f'padding:9px 0; border-bottom:1px solid rgba(255,255,255,0.06); align-items:center;">'
                            f'<div style="color:#E7EEF9; font-weight:900; font-size:0.78rem;">{t1}/{t2}</div>'
                            f'<div style="color:{color}; font-weight:950;">{c:.2f}</div>'
                            f'<div style="color:{color}; font-size:0.72rem;">{"Fail Together" if c >= 0.75 else "Monitor"}</div>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:315px; padding:14px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:10px;">'
                            f'PAIR FAILURE WATCHLIST'
                        f'</div>'
                        f'{watch_rows}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with bottom_right:
                st.markdown("### AI Correlation Interpretation")

                corr_read = (
                    f"[Correlation Desk Read]<br>"
                    f"Book correlation state is <b style='color:{corr_color};'>{corr_state}</b>. "
                    f"Average pair correlation sits at <b>{avg_corr:.2f}</b>, with <b>{cluster_count}</b> high-correlation clusters detected.<br><br>"

                    f"[Hidden Concentration]<br>"
                    f"Highest pair correlation is <b style='color:#FF4D6D;'>{corr_pairs[0][0]} / {corr_pairs[0][1]} at {corr_pairs[0][2]:.2f}</b>. "
                    f"Headline allocation may overstate diversification if these pairs compress further under volatility stress.<br><br>"

                    f"[Hedge Integrity]<br>"
                    f"Hedge pair count registers at <b style='color:#73CFFF;'>{hedge_pairs}</b>. "
                    f"Defensive ballast is useful only if inverse or low-correlation behavior survives the shock window.<br><br>"

                    f"[AI Correlation Directive]<br>"
                    f"Treat highly correlated growth sleeves as one risk block; preserve hedge dispersion before adding exposure."
                )

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:315px; padding:16px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                            f'<div style="font-size:0.78rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em;">AI CORRELATION INTERPRETATION</div>'
                            f'<div style="font-size:0.72rem; color:#2EE59D; font-weight:900;">LIVE CORRELATION READ</div>'
                        f'</div>'
                        f'<div style="color:#E7EEF9; font-size:0.88rem; line-height:1.62;">{corr_read}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown(
                f'<div class="portfolio-card" style="margin-top:10px; padding:10px 14px; display:flex; justify-content:center; gap:28px; '
                f'color:rgba(231,238,249,0.68); font-size:0.78rem;">'
                    f'<span style="color:#2EE59D; font-weight:950;">CORRELATION MODEL LIVE</span>'
                    f'<span>State: {corr_state}</span>'
                    f'<span>Avg Corr: {avg_corr:.2f}</span>'
                    f'<span>Clusters: {cluster_count}</span>'
                    f'<span>Diversification: {diversification_score:.0f}/100</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.stop()

        if selected_view == "Scenario Engine":
            scenario_presets = {
                "Inflation Reacceleration": {
                    "growth": -1.0, "inflation": 3.5, "rates": 2.0, "oil": 18.0, "usd": 4.0,
                    "credit": 1.2, "ai_spend": -8.0, "spy": -12.0, "vol": 1.45,
                    "regime": "Persistent Inflation Regime",
                    "color": "#FFB020",
                },
                "AI Capex Deceleration": {
                    "growth": -0.5, "inflation": 0.4, "rates": -0.2, "oil": -2.0, "usd": 1.5,
                    "credit": 0.8, "ai_spend": -28.0, "spy": -9.0, "vol": 1.35,
                    "regime": "Multiple Compression Cycle",
                    "color": "#FF4D6D",
                },
                "Liquidity Crisis": {
                    "growth": -2.0, "inflation": -0.5, "rates": -1.0, "oil": -10.0, "usd": 6.0,
                    "credit": 3.0, "ai_spend": -15.0, "spy": -24.0, "vol": 2.10,
                    "regime": "Liquidity Stress Regime",
                    "color": "#FF4D6D",
                },
                "Geopolitical Supply Shock": {
                    "growth": -1.2, "inflation": 2.8, "rates": 1.0, "oil": 35.0, "usd": 5.0,
                    "credit": 1.4, "ai_spend": -6.0, "spy": -14.0, "vol": 1.65,
                    "regime": "Geopolitical Supply Shock",
                    "color": "#FF4D6D",
                },
                "Global Demand Shock": {
                    "growth": -3.0, "inflation": -1.5, "rates": -2.0, "oil": -22.0, "usd": 3.5,
                    "credit": 2.2, "ai_spend": -12.0, "spy": -20.0, "vol": 1.85,
                    "regime": "Demand Contraction Regime",
                    "color": "#73CFFF",
                },
                "Credit Contagion Event": {
                    "growth": -2.3, "inflation": -0.8, "rates": -1.5, "oil": -14.0, "usd": 7.0,
                    "credit": 3.8, "ai_spend": -18.0, "spy": -27.0, "vol": 2.25,
                    "regime": "Credit Contagion Event",
                    "color": "#FF4D6D",
                },
                "Soft Landing / Melt-Up": {
                    "growth": 1.4, "inflation": -0.7, "rates": -0.8, "oil": -3.0, "usd": -2.0,
                    "credit": -0.5, "ai_spend": 12.0, "spy": 14.0, "vol": 0.80,
                    "regime": "Risk-On Expansion",
                    "color": "#2EE59D",
                },
            }

            st.markdown(
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<div>'
                            f'<div style="font-size:1.75rem; font-weight:950; color:#E7EEF9;">Scenario Engine</div>'
                            f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">'
                                f'Macro scenario transmission, regime shift, and portfolio survivability modeling.'
                            f'</div>'
                        f'</div>'
                        f'<div style="text-align:right;">'
                            f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.52);">SCENARIO MODEL</div>'
                            f'<div style="font-size:1rem; color:#2EE59D; font-weight:900;">LIVE</div>'
                        f'</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            control_cols = st.columns([1.35, 1, 1, 1, 1], gap="medium")

            with control_cols[0]:
                selected_scenario = st.selectbox(
                    "Scenario Preset",
                    list(scenario_presets.keys()),
                    key="scenario_engine_preset"
                )

            base_scenario = scenario_presets[selected_scenario]

            with control_cols[1]:
                custom_growth = st.slider("GDP Growth Shock", -5.0, 3.0, float(base_scenario["growth"]), 0.1, key="scenario_growth")

            with control_cols[2]:
                custom_inflation = st.slider("Inflation Shock", -3.0, 5.0, float(base_scenario["inflation"]), 0.1, key="scenario_inflation")

            with control_cols[3]:
                custom_rates = st.slider("Rates Shock", -3.0, 3.0, float(base_scenario["rates"]), 0.1, key="scenario_rates")

            with control_cols[4]:
                custom_ai_spend = st.slider("AI Spend Shock", -40.0, 25.0, float(base_scenario["ai_spend"]), 1.0, key="scenario_ai_spend")

            scenario = base_scenario.copy()
            scenario["growth"] = custom_growth
            scenario["inflation"] = custom_inflation
            scenario["rates"] = custom_rates
            scenario["ai_spend"] = custom_ai_spend

            scenario_intensity = (
                abs(scenario["growth"]) * 9
                + abs(scenario["inflation"]) * 7
                + abs(scenario["rates"]) * 8
                + abs(scenario["credit"]) * 10
                + abs(scenario["ai_spend"]) * 0.7
                + abs(scenario["spy"]) * 1.2
            )
            scenario_intensity = max(0, min(100, scenario_intensity))

            scenario_prob = min(85, max(8, 18 + scenario_intensity * 0.45))
            vol_shift = (scenario["vol"] - 1) * 100

            scenario_tickers = [p["ticker"] for p in recommendations if p["ticker"] != "CASH"]
            scenario_total = sum(p["dollars"] for p in recommendations if p["ticker"] != "CASH")
            scenario_weights = {
                p["ticker"]: p["dollars"] / scenario_total
                for p in recommendations
                if p["ticker"] != "CASH"
            }

            scenario_reactions = {}

            for ticker, weight in scenario_weights.items():
                impact = scenario["spy"] * 0.65

                if ticker in ["SPY", "VTI"]:
                    impact += scenario["spy"] * 0.35

                if ticker in ["QQQ", "NVDA", "MSFT", "AMZN", "SMH", "TSLA"]:
                    impact += scenario["ai_spend"] * 0.35
                    impact += scenario["rates"] * -3.8
                    impact += scenario["credit"] * -2.0

                if ticker in ["MSTR", "TSLA"]:
                    impact += scenario["vol"] * -5.5
                    impact += scenario["credit"] * -2.8

                if ticker in ["TLT"]:
                    impact += scenario["rates"] * -7.0
                    impact += scenario["growth"] * -2.0

                if ticker in ["GLD"]:
                    impact += scenario["inflation"] * 2.2
                    impact += scenario["oil"] * 0.12
                    impact += scenario["usd"] * -0.7

                if ticker in ["SHY"]:
                    impact += -1.0 if scenario["credit"] > 2 else 0.5

                scenario_reactions[ticker] = impact

            portfolio_impact = sum(
                scenario_reactions[ticker] * weight
                for ticker, weight in scenario_weights.items()
            )

            stressed_value = portfolio_size * (1 + portfolio_impact / 100)
            dollar_impact = portfolio_size - stressed_value
            spy_gap = portfolio_impact - scenario["spy"]

            recovery_months = max(3, min(48, int(8 + scenario_intensity * 0.38)))
            tail_risk = min(100, scenario_intensity * 0.85 + max(0, -portfolio_impact) * 0.8)
            survival_score = max(0, min(100, 100 - tail_risk + max(0, scenario_weights.get("TLT", 0) + scenario_weights.get("GLD", 0) + scenario_weights.get("SHY", 0)) * 35))

            survival_color = "#2EE59D" if survival_score >= 70 else "#FFB020" if survival_score >= 45 else "#FF4D6D"
            tail_color = "#FF4D6D" if tail_risk >= 70 else "#FFB020" if tail_risk >= 40 else "#2EE59D"
            impact_color = "#2EE59D" if portfolio_impact >= 0 else "#FFB020" if portfolio_impact > -10 else "#FF4D6D"

            first_failure = "growth multiple compression" if scenario["ai_spend"] < -10 or scenario["rates"] > 1 else "equity beta drawdown" if scenario["spy"] < -10 else "macro factor drift"
            beneficiary = "GLD / SHY defense sleeve" if scenario["inflation"] > 1 or scenario["credit"] > 2 else "TLT duration sleeve" if scenario["rates"] < -1 else "growth sleeve"
            regime_shift = scenario["regime"]

            metric_cards = [
                ("Scenario Prob.", f"{scenario_prob:.0f}%", "#73CFFF"),
                ("Portfolio Impact", f"{portfolio_impact:+.1f}%", impact_color),
                ("Stressed Value", f"${stressed_value:,.0f}", "#E7EEF9"),
                ("SPY Gap", f"{spy_gap:+.1f}%", "#FFB020"),
                ("Vol Shift", f"{vol_shift:+.0f}%", "#FF4D6D" if vol_shift > 25 else "#2EE59D"),
                ("Recovery Window", f"{recovery_months} mo", "#73CFFF"),
                ("Tail Risk", f"{tail_risk:.0f}/100", tail_color),
                ("Survival Score", f"{survival_score:.0f}/100", survival_color),
            ]

            metric_html = (
                f'<div style="display:grid; grid-template-columns:repeat(8, minmax(0, 1fr)); gap:10px; margin-top:14px; margin-bottom:14px;">'
            )

            for label, value, color in metric_cards:
                metric_html += (
                    f'<div class="metric-tile" style="min-height:105px; padding:14px;">'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-value" style="color:{color}; font-size:1.22rem;">{value}</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:12px; overflow:hidden;">'
                            f'<div style="width:78%; height:100%; background:{color}; border-radius:999px;"></div>'
                        f'</div>'
                    f'</div>'
                )

            metric_html += f'</div>'
            st.markdown(metric_html, unsafe_allow_html=True)
              
            upper_left, upper_right = st.columns([1.0, 1.35], gap="medium")

            with upper_left:
                st.markdown("### Scenario Transmission")

                transmission_rows = [
                    ("First Failure Point", first_failure, "#FF4D6D"),
                    ("Primary Beneficiary", beneficiary, "#2EE59D"),
                    ("Regime Shift", regime_shift, "#73CFFF"),
                    ("Volatility Expansion", f"{vol_shift:+.0f}%", "#FF4D6D"),
                    ("Liquidity Pressure", "Elevated" if scenario["credit"] > 2 else "Moderate", "#FFB020"),
                ]

                transmission_html = (
                    f'<div class="portfolio-card" style="min-height:300px; padding:16px;">'
                    f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">SCENARIO TRANSMISSION MAP</div>'
                )

                for label, value, color in transmission_rows:
                    transmission_html += (
                        f'<div style="margin-bottom:12px;">'
                        f'<div style="display:flex; justify-content:space-between; font-size:0.82rem;">'
                        f'<span>{label}</span><b style="color:{color};">{value}</b>'
                        f'</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                        f'<div style="width:78%; height:100%; background:{color}; border-radius:999px;"></div>'
                        f'</div>'
                        f'</div>'
                    )

                transmission_html += f'</div>'
                st.markdown(transmission_html, unsafe_allow_html=True)

                st.markdown("### Macro Pressure Map")

                macro_rows = [
                    ("GDP Shock", scenario["growth"], "#FF4D6D" if scenario["growth"] < 0 else "#2EE59D"),
                    ("Inflation", scenario["inflation"], "#FFB020"),
                    ("Rates", scenario["rates"], "#73CFFF"),
                    ("Oil", scenario["oil"], "#FF4D6D" if scenario["oil"] > 10 else "#2EE59D"),
                    ("USD", scenario["usd"], "#73CFFF"),
                    ("Credit Stress", scenario["credit"], "#FF4D6D"),
                    ("AI Spending", scenario["ai_spend"], "#FF4D6D" if scenario["ai_spend"] < 0 else "#2EE59D"),
                ]

                macro_html = (
                    f'<div class="portfolio-card" style="min-height:300px; padding:16px;">'
                    f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">MACRO PRESSURE STACK</div>'
                )

                for label, value, color in macro_rows:
                    width = min(100, max(5, abs(value) * 12))
                    macro_html += (
                        f'<div style="margin-bottom:10px;">'
                        f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                        f'<span>{label}</span><b style="color:{color};">{value:+.1f}</b>'
                        f'</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                        f'<div style="width:{width:.1f}%; height:100%; background:{color}; border-radius:999px;"></div>'
                        f'</div>'
                        f'</div>'
                    )

                macro_html += f'</div>'
                st.markdown(macro_html, unsafe_allow_html=True)

            with upper_right:
                st.markdown("### Scenario Outcome Matrix")

                sorted_reactions = sorted(scenario_reactions.items(), key=lambda x: x[1])

                outcome_html = (
                    f'<div class="portfolio-card" style="min-height:300px; padding:16px;">'
                    f'<div style="display:grid; grid-template-columns:0.8fr 0.8fr 0.8fr 1fr; gap:10px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:8px; font-size:0.68rem; color:rgba(231,238,249,0.52); font-weight:900;">'
                    f'<div>ASSET</div><div>MOVE</div><div>REGIME</div><div>IMPACT INTENSITY</div>'
                    f'</div>'
                )

                for ticker, impact in sorted_reactions[:8]:
                    if impact <= -20:
                        color = "#FF4D6D"      # crisis
                    elif impact <= -8:
                        color = "#FFB020"      # stress
                    elif impact < 0:
                        color = "#73CFFF"      # moderate/system
                    else:
                        color = "#2EE59D"      # positive
                    regime_tag = "Defense" if ticker in ["TLT", "GLD", "SHY"] else "Growth"
                    width = min(100, max(5, abs(impact) * 3))

                    outcome_html += (
                        f'<div style="display:grid; grid-template-columns:0.8fr 0.8fr 0.8fr 1fr; gap:10px; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05); align-items:center;">'
                        f'<div style="font-weight:950;">{ticker}</div>'
                        f'<div style="color:{color}; font-weight:950;">{impact:+.1f}%</div>'
                        f'<div style="color:rgba(231,238,249,0.70); font-size:0.74rem;">{regime_tag}</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); overflow:hidden;">'
                        f'<div style="width:{width:.1f}%; height:100%; background:{color}; border-radius:999px;"></div>'
                        f'</div>'
                        f'</div>'
                    )

                outcome_html += f'</div>'
                st.markdown(outcome_html, unsafe_allow_html=True)

                st.markdown("### Portfolio Survivability")

                survivability_html = (
                    f'<div class="portfolio-card" style="min-height:300px; padding:16px;">'
                    f'<div style="display:grid; grid-template-columns:0.7fr 1.3fr; gap:18px; align-items:center;">'
                    f'<div style="text-align:center;">'
                    f'<div style="margin:0 auto; width:145px; height:145px; border-radius:50%; background:conic-gradient({survival_color} 0deg, {survival_color} {survival_score * 3.6:.0f}deg, rgba(255,255,255,0.08) {survival_score * 3.6:.0f}deg); display:flex; align-items:center; justify-content:center;">'
                    f'<div style="width:102px; height:102px; border-radius:50%; background:#091733; display:flex; flex-direction:column; align-items:center; justify-content:center;">'
                    f'<div style="font-size:2rem; color:{survival_color}; font-weight:950;">{survival_score:.0f}</div>'
                    f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.58);">/100</div>'
                    f'</div></div>'
                    f'<div style="margin-top:8px; font-size:0.72rem; color:rgba(231,238,249,0.55); font-weight:900;">SURVIVAL SCORE</div>'
                    f'</div>'
                    f'<div>'
                    f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Tail Risk</span><b style="color:{tail_color};">{tail_risk:.0f}/100</b></div>'
                    f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Recovery Window</span><b style="color:#73CFFF;">{recovery_months} mo</b></div>'
                    f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Liquidity Integrity</span><b style="color:#FFB020;">{"Fragile" if scenario["credit"] > 2 else "Stable"}</b></div>'
                    f'<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span>Defense Response</span><b style="color:#2EE59D;">Partial Offset</b></div>'
                    f'<div style="display:flex; justify-content:space-between;"><span>Scenario Severity</span><b style="color:{tail_color};">{scenario_intensity:.0f}/100</b></div>'
                    f'</div>'
                    f'</div>'
                    f'</div>'
                )

                st.markdown(survivability_html, unsafe_allow_html=True)

            # -----------------------------
            # AI Scenario Interpretation - full width
            # -----------------------------
            st.markdown("### AI Scenario Interpretation")

            scenario_read = (
                f"[Scenario Desk Read]<br>"
                f"Current scenario path implies <b style='color:{base_scenario['color']};'>{regime_shift}</b>. "
                f"Portfolio impact projects at <b style='color:{impact_color};'>{portfolio_impact:+.1f}%</b>, "
                f"with survivability score currently registering at <b>{survival_score:.0f}/100</b>.<br><br>"

                f"[Transmission Path]<br>"
                f"Primary stress transmission flows through <b style='color:#FF4D6D;'>{first_failure}</b>. "
                f"Volatility expansion and factor compression intensify as liquidity conditions weaken and cross-asset dispersion narrows.<br><br>"

                f"[Defense Integrity]<br>"
                f"Defensive ballast response remains <b style='color:#2EE59D;'>partial</b>. "
                f"{beneficiary} acts as the primary stabilizing sleeve, though protection weakens if correlation compression accelerates.<br><br>"

                f"[Macro Pressure]<br>"
                f"Macro stack reflects GDP shock of <b>{scenario['growth']:+.1f}</b>, inflation shift of "
                f"<b>{scenario['inflation']:+.1f}</b>, and AI spending shock of <b>{scenario['ai_spend']:+.0f}%</b>.<br><br>"

                f"[AI Scenario Directive]<br>"
                f"Reduce concentrated beta exposure during regime instability. Preserve liquidity optionality until volatility normalization and macro dispersion stabilize."
            )

            st.markdown(
                f'<div class="portfolio-card" style="min-height:210px; padding:16px;">'
                    f'<div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:0; border-top:1px solid rgba(255,255,255,0.08);">'
                        f'<div style="padding:14px; border-right:1px solid rgba(255,255,255,0.08);"><b style="color:#73CFFF;">Scenario Desk Read</b><br><br>{scenario_read.split("<br><br>")[0]}</div>'
                        f'<div style="padding:14px; border-right:1px solid rgba(255,255,255,0.08);"><b style="color:#FF4D6D;">Transmission Path</b><br><br>{scenario_read.split("<br><br>")[1]}</div>'
                        f'<div style="padding:14px; border-right:1px solid rgba(255,255,255,0.08);"><b style="color:#2EE59D;">Defense Integrity</b><br><br>{scenario_read.split("<br><br>")[2]}</div>'
                        f'<div style="padding:14px; border-right:1px solid rgba(255,255,255,0.08);"><b style="color:#FFB020;">Macro Pressure</b><br><br>{scenario_read.split("<br><br>")[3]}</div>'
                        f'<div style="padding:14px;"><b style="color:#2EE59D;">AI Scenario Directive</b><br><br>{scenario_read.split("<br><br>")[4]}</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="portfolio-card" style="margin-top:10px; padding:10px 14px; display:flex; justify-content:center; gap:28px; color:rgba(231,238,249,0.68); font-size:0.78rem;">'
                    f'<span style="color:#2EE59D; font-weight:950;">SCENARIO MODEL LIVE</span>'
                    f'<span>Preset: {selected_scenario}</span>'
                    f'<span>Regime: {regime_shift}</span>'
                    f'<span>Severity: {scenario_intensity:.0f}/100</span>'
                    f'<span>Recovery: {recovery_months} mo</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.stop()

        if selected_view == "AI Recommendations":
            # -----------------------------
            # AI Recommendations — Portfolio Action Layer
            # -----------------------------

            rec_tickers = [p["ticker"] for p in recommendations if p["ticker"] != "CASH"]
            rec_total = sum(p["dollars"] for p in recommendations if p["ticker"] != "CASH")

            rec_weights = {
                p["ticker"]: p["dollars"] / rec_total
                for p in recommendations
                if p["ticker"] != "CASH"
            }

            growth_names = ["QQQ", "NVDA", "MSFT", "AMZN", "SMH", "TSLA", "MSTR"]
            defense_names = ["TLT", "GLD", "SHY"]
            beta_names = ["SPY", "VTI", "QQQ"]

            growth_weight = sum(rec_weights.get(t, 0) for t in growth_names) * 100
            defense_weight = sum(rec_weights.get(t, 0) for t in defense_names) * 100
            beta_weight = sum(rec_weights.get(t, 0) for t in beta_names) * 100

            rec_vol_state = "Contained" if market_regime["vix"] < 18 else "Elevated" if market_regime["vix"] < 25 else "Stress"
            rec_regime_score = market_regime["score"]

            action_bias = "Add Risk" if rec_regime_score >= 75 and rec_vol_state == "Contained" else "Hold / Rebalance" if rec_regime_score >= 55 else "De-Risk"
            action_color = "#2EE59D" if action_bias == "Add Risk" else "#FFB020" if action_bias == "Hold / Rebalance" else "#FF4D6D"

            hedge_need = "Low" if defense_weight >= 20 else "Moderate" if defense_weight >= 10 else "High"
            hedge_color = "#2EE59D" if hedge_need == "Low" else "#FFB020" if hedge_need == "Moderate" else "#FF4D6D"

            crowding_level = "High" if growth_weight >= 45 else "Moderate" if growth_weight >= 25 else "Low"
            crowding_color = "#FF4D6D" if crowding_level == "High" else "#FFB020" if crowding_level == "Moderate" else "#2EE59D"

            liquidity_need = "Preserve" if rec_vol_state != "Contained" or rec_regime_score < 60 else "Normal"
            liquidity_color = "#FFB020" if liquidity_need == "Preserve" else "#2EE59D"

            recommendation_score = 78
            recommendation_score -= 12 if crowding_level == "High" else 4 if crowding_level == "Moderate" else 0
            recommendation_score -= 10 if rec_vol_state == "Elevated" else 22 if rec_vol_state == "Stress" else 0
            recommendation_score += 8 if rec_regime_score >= 70 else 0
            recommendation_score = max(0, min(100, recommendation_score))

            recommendation_color = "#2EE59D" if recommendation_score >= 75 else "#FFB020" if recommendation_score >= 55 else "#FF4D6D"

            # -----------------------------
            # Suggested target weights
            # -----------------------------
            suggested_weights = {}

            for ticker, weight in rec_weights.items():
                current_pct = weight * 100
                suggested = current_pct

                if ticker in growth_names and crowding_level == "High":
                    suggested *= 0.82
                elif ticker in growth_names and rec_vol_state == "Elevated":
                    suggested *= 0.92

                if ticker in defense_names and hedge_need in ["Moderate", "High"]:
                    suggested *= 1.18

                if ticker in ["SHY"] and liquidity_need == "Preserve":
                    suggested *= 1.35

                if ticker in beta_names and rec_regime_score >= 70 and rec_vol_state == "Contained":
                    suggested *= 1.08

                suggested_weights[ticker] = suggested

            raw_total = sum(suggested_weights.values())

            if raw_total > 0:
                suggested_weights = {
                    ticker: value / raw_total * 100
                    for ticker, value in suggested_weights.items()
                }

            # -----------------------------
            # Header
            # -----------------------------
            st.markdown(
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<div>'
                            f'<div style="font-size:1.75rem; font-weight:950; color:#E7EEF9;">AI Recommendations</div>'
                            f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">'
                                f'Portfolio action layer translating risk, factor, regime, and scenario signals into tactical adjustments.'
                            f'</div>'
                        f'</div>'
                        f'<div style="text-align:right;">'
                            f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.52);">AI ACTION MODEL</div>'
                            f'<div style="font-size:1rem; color:#2EE59D; font-weight:900;">LIVE</div>'
                        f'</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            rec_metrics = [
                ("Action Bias", action_bias, action_color),
                ("Recommendation Score", f"{recommendation_score}/100", recommendation_color),
                ("Growth Load", f"{growth_weight:.0f}%", crowding_color),
                ("Defense Load", f"{defense_weight:.0f}%", hedge_color),
                ("Liquidity Bias", liquidity_need, liquidity_color),
                ("Regime", market_regime["regime"], market_regime["color"]),
            ]

            metric_html = (
                f'<div style="display:grid; grid-template-columns:repeat(6, minmax(0, 1fr)); '
                f'gap:10px; margin-top:14px; margin-bottom:14px;">'
            )

            for label, value, color in rec_metrics:
                metric_html += (
                    f'<div class="metric-tile" style="min-height:105px; padding:14px;">'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-value" style="color:{color}; font-size:1.12rem;">{value}</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:12px; overflow:hidden;">'
                            f'<div style="width:78%; height:100%; background:{color}; border-radius:999px;"></div>'
                        f'</div>'
                    f'</div>'
                )

            metric_html += '</div>'
            st.markdown(metric_html, unsafe_allow_html=True)

            # -----------------------------
            # Main layout
            # -----------------------------
            left_col, right_col = st.columns([1.1, 1.35], gap="medium")

            with left_col:
                st.markdown("### Portfolio Action Stack")

                action_rows = [
                    ("Beta Exposure", "Hold" if action_bias != "De-Risk" else "Trim", beta_weight, "#73CFFF"),
                    ("Growth / AI Sleeve", "Trim" if crowding_level == "High" else "Hold", growth_weight, crowding_color),
                    ("Defense Sleeve", "Add" if hedge_need in ["Moderate", "High"] else "Hold", defense_weight, hedge_color),
                    ("Liquidity Sleeve", "Add" if liquidity_need == "Preserve" else "Hold", rec_weights.get("SHY", 0) * 100, liquidity_color),
                    ("High Beta / Convexity", "Trim" if rec_vol_state != "Contained" else "Watch", sum(rec_weights.get(t, 0) for t in ["MSTR", "TSLA", "NVDA", "SMH"]) * 100, "#FFB020"),
                ]

                action_html = (
                    f'<div class="portfolio-card" style="min-height:350px; padding:16px;">'
                    f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">TACTICAL ACTION MAP</div>'
                )

                for sleeve, action, score, color in action_rows:
                    action_html += (
                        f'<div style="padding:11px 12px; margin-bottom:10px; border-radius:14px; background:{color}16; border:1px solid {color}44;">'
                            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                                f'<div style="font-weight:950; color:#E7EEF9;">{sleeve}</div>'
                                f'<div style="color:{color}; font-weight:950;">{action}</div>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:8px; overflow:hidden;">'
                                f'<div style="width:{min(100, max(5, score * 1.4)):.1f}%; height:100%; background:{color}; border-radius:999px;"></div>'
                            f'</div>'
                        f'</div>'
                    )

                action_html += '</div>'
                st.markdown(action_html, unsafe_allow_html=True)

                st.markdown("### Tradeoff Analysis")

                tradeoff_html = (
                    f'<div class="portfolio-card" style="min-height:260px; padding:16px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">PM TRADEOFF MAP</div>'
                        f'<div style="display:grid; gap:10px;">'
                            f'<div style="display:flex; justify-content:space-between;"><span>Expected Return Pressure</span><b style="color:#FFB020;">Moderate</b></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Survivability Improvement</span><b style="color:#2EE59D;">Positive</b></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Correlation Relief</span><b style="color:#73CFFF;">Partial</b></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Liquidity Optionality</span><b style="color:{liquidity_color};">{liquidity_need}</b></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Upside Sacrifice</span><b style="color:#FFB020;">Controlled</b></div>'
                        f'</div>'
                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:16px 0;"></div>'
                        f'<div style="font-size:0.82rem; color:rgba(231,238,249,0.70); line-height:1.55;">'
                            f'Recommendation layer prioritizes cleaner risk posture without fully abandoning the active regime bias.'
                        f'</div>'
                    f'</div>'
                )

                st.markdown(tradeoff_html, unsafe_allow_html=True)

            with right_col:
                st.markdown("### Position Adjustment Engine")

                adjustment_html = (
                    f'<div class="portfolio-card" style="min-height:350px; padding:16px;">'
                    f'<div style="display:grid; grid-template-columns:0.8fr 0.75fr 0.75fr 0.75fr 1fr; gap:10px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:8px; font-size:0.68rem; color:rgba(231,238,249,0.52); font-weight:900;">'
                    f'<div>ASSET</div><div>CURRENT</div><div>SUGGESTED</div><div>ACTION</div><div>REASON</div>'
                    f'</div>'
                )

                for ticker, current_weight in sorted(rec_weights.items(), key=lambda x: x[1], reverse=True):
                    current_pct = current_weight * 100
                    suggested_pct = suggested_weights.get(ticker, current_pct)
                    delta = suggested_pct - current_pct

                    if delta > 0.75:
                        action = "Add"
                        color = "#2EE59D"
                    elif delta < -0.75:
                        action = "Trim"
                        color = "#FF4D6D"
                    else:
                        action = "Hold"
                        color = "#73CFFF"

                    if ticker in growth_names:
                        reason = "growth beta"
                    elif ticker in defense_names:
                        reason = "defense ballast"
                    elif ticker in beta_names:
                        reason = "core beta"
                    else:
                        reason = "idiosyncratic"

                    adjustment_html += (
                        f'<div style="display:grid; grid-template-columns:0.8fr 0.75fr 0.75fr 0.75fr 1fr; gap:10px; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05); align-items:center;">'
                            f'<div style="font-weight:950; color:#E7EEF9;">{ticker}</div>'
                            f'<div>{current_pct:.1f}%</div>'
                            f'<div style="color:{color}; font-weight:950;">{suggested_pct:.1f}%</div>'
                            f'<div style="color:{color}; font-weight:950;">{action}</div>'
                            f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.68);">{reason}</div>'
                        f'</div>'
                    )

                adjustment_html += '</div>'
                st.markdown(adjustment_html, unsafe_allow_html=True)

                st.markdown("### Tactical Theme Board")

                theme_rows = [
                    ("AI Infrastructure", "Constructive", 82, "#2EE59D"),
                    ("Liquidity Preservation", "High Priority", 76, liquidity_color),
                    ("Defense Rotation", "Selective", 62, hedge_color),
                    ("High Beta Chase", "Avoid", 28, "#FF4D6D"),
                    ("Duration Hedge", "Conditional", 48, "#73CFFF"),
                ]

                theme_html = (
                    f'<div class="portfolio-card" style="min-height:260px; padding:16px;">'
                    f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">TACTICAL THEMES</div>'
                )

                for theme, state, score, color in theme_rows:
                    theme_html += (
                        f'<div style="margin-bottom:13px;">'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                                f'<span>{theme}</span>'
                                f'<b style="color:{color};">{state}</b>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                                f'<div style="width:{score}%; height:100%; background:{color}; border-radius:999px;"></div>'
                            f'</div>'
                        f'</div>'
                    )

                theme_html += '</div>'
                st.markdown(theme_html, unsafe_allow_html=True)

            # -----------------------------
            # AI Recommendation Desk Read
            # -----------------------------
            st.markdown("### AI Recommendation Desk")

            rec_read = (
                f"[Action Read]<br>"
                f"Current action bias is <b style='color:{action_color};'>{action_bias}</b>. "
                f"Book remains exposed to {growth_weight:.0f}% growth-linked risk with {defense_weight:.0f}% defensive ballast. "
                f"Recommendation score sits at <b style='color:{recommendation_color};'>{recommendation_score}/100</b>.<br><br>"

                f"[Portfolio Adjustment]<br>"
                f"Primary adjustment path is to preserve core beta while controlling crowded growth exposure. "
                f"Defense sleeve should remain active as long as volatility state is <b>{rec_vol_state}</b> and correlation risk is not fully resolved.<br><br>"

                f"[Tradeoff]<br>"
                f"Reducing high-beta exposure may cap some upside, but improves liquidity optionality, survivability, and drawdown control under regime instability.<br><br>"

                f"[AI Recommendation Directive]<br>"
                f"Do not chase additional beta until dispersion quality improves. Keep the book liquid, balanced, and regime-aware."
            )

            st.markdown(
                f'<div class="portfolio-card" style="min-height:230px; padding:16px;">'
                    f'<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:0; border-top:1px solid rgba(255,255,255,0.08);">'
                        f'<div style="padding:14px; border-right:1px solid rgba(255,255,255,0.08);"><b style="color:{action_color};">Action Read</b><br><br>{rec_read.split("<br><br>")[0]}</div>'
                        f'<div style="padding:14px; border-right:1px solid rgba(255,255,255,0.08);"><b style="color:#73CFFF;">Portfolio Adjustment</b><br><br>{rec_read.split("<br><br>")[1]}</div>'
                        f'<div style="padding:14px; border-right:1px solid rgba(255,255,255,0.08);"><b style="color:#FFB020;">Tradeoff</b><br><br>{rec_read.split("<br><br>")[2]}</div>'
                        f'<div style="padding:14px;"><b style="color:#2EE59D;">AI Directive</b><br><br>{rec_read.split("<br><br>")[3]}</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="portfolio-card" style="margin-top:10px; padding:10px 14px; display:flex; justify-content:center; gap:28px; '
                f'color:rgba(231,238,249,0.68); font-size:0.78rem;">'
                    f'<span style="color:#2EE59D; font-weight:950;">AI RECOMMENDATIONS LIVE</span>'
                    f'<span>Action: {action_bias}</span>'
                    f'<span>Growth: {growth_weight:.0f}%</span>'
                    f'<span>Defense: {defense_weight:.0f}%</span>'
                    f'<span>Score: {recommendation_score}/100</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.stop()

        if selected_view == "AI Insights":
            # -----------------------------
            # AI Insights — Trader Desk Layer
            # -----------------------------

            ai_factor_state = "Growth Skew" if "Growth" in portfolio_type or risk_level in ["Medium", "High"] else "Defensive Skew"
            ai_liquidity_state = "Stable" if market_regime["score"] >= 55 else "Thin"
            ai_vol_state = "Contained" if market_regime["vix"] < 18 else "Elevated" if market_regime["vix"] < 25 else "Stress"
            ai_correlation_state = "Compression Watch" if risk_level in ["Medium", "High"] else "Balanced"
            ai_crowding_state = "Moderate" if risk_level == "Medium" else "High" if risk_level == "High" else "Low"
            ai_policy_state = "Rates Sensitive" if "Growth" in portfolio_type else "Policy Neutral"

            insight_score = 82
            insight_score -= 12 if ai_vol_state == "Elevated" else 0
            insight_score -= 22 if ai_vol_state == "Stress" else 0
            insight_score -= 10 if ai_crowding_state == "High" else 0
            insight_score += 6 if market_regime["score"] >= 70 else 0
            insight_score = max(0, min(100, insight_score))

            insight_color = "#2EE59D" if insight_score >= 75 else "#FFB020" if insight_score >= 55 else "#FF4D6D"

            desk_thesis = (
                f"Book remains positioned for {market_regime['regime'].lower()} with {ai_factor_state.lower()} "
                f"and {ai_crowding_state.lower()} crowding pressure. Defensive ballast is present, but the portfolio "
                f"still depends on equity beta, growth leadership, and contained volatility."
            )

            alert_rows = [
                ("REGIME", market_regime["regime"], market_regime["color"], "Macro tape still defines downstream risk assumptions."),
                ("FACTOR", ai_factor_state, "#73CFFF", "Current allocation leans into growth/market beta transmission."),
                ("CORRELATION", ai_correlation_state, "#FFB020", "Diversification quality depends on dispersion holding up."),
                ("VOLATILITY", ai_vol_state, "#FF4D6D" if ai_vol_state == "Stress" else "#FFB020" if ai_vol_state == "Elevated" else "#2EE59D", "Vol expansion would pressure convexity and survivability."),
                ("LIQUIDITY", ai_liquidity_state, "#2EE59D" if ai_liquidity_state == "Stable" else "#FF4D6D", "Liquidity condition affects recovery and rebalance flexibility."),
            ]

            st.markdown(
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<div>'
                            f'<div style="font-size:1.75rem; font-weight:950; color:#E7EEF9;">AI Insights</div>'
                            f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">'
                                f'Trader-desk intelligence layer across regime, factor, risk, correlation, and scenario signals.'
                            f'</div>'
                        f'</div>'
                        f'<div style="text-align:right;">'
                            f'<div style="font-size:0.7rem; color:rgba(231,238,249,0.52);">AI DESK MODEL</div>'
                            f'<div style="font-size:1rem; color:#2EE59D; font-weight:900;">LIVE</div>'
                        f'</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            insight_metrics = [
                ("Desk Conviction", f"{insight_score}/100", insight_color),
                ("Regime", market_regime["regime"], market_regime["color"]),
                ("Vol State", ai_vol_state, "#2EE59D" if ai_vol_state == "Contained" else "#FFB020"),
                ("Crowding", ai_crowding_state, "#FFB020"),
                ("Liquidity", ai_liquidity_state, "#2EE59D"),
                ("Policy", ai_policy_state, "#73CFFF"),
            ]

            metric_html = '<div style="display:grid; grid-template-columns:repeat(6, minmax(0, 1fr)); gap:10px; margin-top:14px; margin-bottom:14px;">'

            for label, value, color in insight_metrics:
                metric_html += (
                    f'<div class="metric-tile" style="min-height:105px; padding:14px;">'
                        f'<div class="metric-label">{label}</div>'
                        f'<div class="metric-value" style="color:{color}; font-size:1.15rem;">{value}</div>'
                        f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:12px; overflow:hidden;">'
                            f'<div style="width:78%; height:100%; background:{color}; border-radius:999px;"></div>'
                        f'</div>'
                    f'</div>'
                )

            metric_html += '</div>'
            st.markdown(metric_html, unsafe_allow_html=True)

            left_col, right_col = st.columns([1.25, 1.35], gap="medium")

            with left_col:
                st.markdown("### Portfolio State Read")

                st.markdown(
                    f'<div class="portfolio-card" style="min-height:310px; padding:18px;">'
                        f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">'
                            f'INTERNAL TRADER DESK'
                        f'</div>'
                        f'<div style="font-size:1.05rem; line-height:1.65; color:#E7EEF9; font-weight:650;">'
                            f'{desk_thesis}'
                        f'</div>'
                        f'<div style="height:1px; background:rgba(255,255,255,0.08); margin:18px 0;"></div>'
                        f'<div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:10px;">'
                            f'<div style="padding:12px; border-radius:14px; background:rgba(46,229,157,0.08); border:1px solid rgba(46,229,157,0.22);">'
                                f'<div style="font-size:0.65rem; color:rgba(231,238,249,0.55);">PRIMARY SUPPORT</div>'
                                f'<div style="color:#2EE59D; font-weight:950; margin-top:5px;">Regime + liquidity</div>'
                            f'</div>'
                            f'<div style="padding:12px; border-radius:14px; background:rgba(255,77,109,0.08); border:1px solid rgba(255,77,109,0.22);">'
                                f'<div style="font-size:0.65rem; color:rgba(231,238,249,0.55);">PRIMARY RISK</div>'
                                f'<div style="color:#FF4D6D; font-weight:950; margin-top:5px;">Beta compression</div>'
                            f'</div>'
                        f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                st.markdown("### Cross-Engine Alerts")

                alert_html = (
                    f'<div class="portfolio-card" style="min-height:330px; padding:16px;">'
                    f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">SIGNAL STACK</div>'
                )

                for label, value, color, note in alert_rows:
                    alert_html += (
                        f'<div style="padding:11px 12px; margin-bottom:10px; border-radius:14px; background:{color}16; border:1px solid {color}44;">'
                            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                                f'<div style="font-size:0.68rem; color:rgba(231,238,249,0.55); font-weight:900; letter-spacing:0.08em;">{label}</div>'
                                f'<div style="color:{color}; font-weight:950;">{value}</div>'
                            f'</div>'
                            f'<div style="font-size:0.76rem; color:rgba(231,238,249,0.68); margin-top:6px;">{note}</div>'
                        f'</div>'
                    )

                alert_html += '</div>'
                st.markdown(alert_html, unsafe_allow_html=True)

            with right_col:
                st.markdown("### Live Intelligence Feed")

                feed_rows = [
                    ("09:31", "Regime signal remains risk-on; allocation still benefits from growth leadership.", "#2EE59D"),
                    ("09:34", "Correlation compression risk remains active across beta-heavy sleeves.", "#FFB020"),
                    ("09:41", "Defensive ballast offsets part of stress path but does not neutralize growth exposure.", "#73CFFF"),
                    ("09:47", "Scenario layer flags AI-spend slowdown as the main downside transmission channel.", "#FF4D6D"),
                    ("09:52", "Risk desk bias: keep liquidity optionality before increasing high-beta exposure.", "#FFB020"),
                ]

                feed_html = (
                    f'<div class="portfolio-card" style="min-height:310px; padding:16px;">'
                    f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">DESK FEED</div>'
                )

                for time_label, text, color in feed_rows:
                    feed_html += (
                        f'<div style="display:grid; grid-template-columns:0.45fr 1fr; gap:12px; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.06);">'
                            f'<div style="color:{color}; font-weight:950;">{time_label}</div>'
                            f'<div style="color:#E7EEF9; font-size:0.82rem; line-height:1.45;">{text}</div>'
                        f'</div>'
                    )

                feed_html += '</div>'
                st.markdown(feed_html, unsafe_allow_html=True)

                st.markdown("### Conviction Matrix")

                conviction_rows = [
                    ("AI Infrastructure", "High", 82, "#2EE59D"),
                    ("Growth Beta", "Positive / crowded", 68, "#FFB020"),
                    ("Duration", "Neutral", 45, "#73CFFF"),
                    ("Gold / Defense", "Useful ballast", 58, "#2EE59D"),
                    ("Liquidity", "Preserve optionality", 72, "#FFB020"),
                    ("Small Caps", "Weak signal", 28, "#FF4D6D"),
                ]

                conviction_html = (
                    f'<div class="portfolio-card" style="min-height:330px; padding:16px;">'
                    f'<div style="font-size:0.72rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em; font-weight:900; margin-bottom:14px;">THEME CONVICTION</div>'
                )

                for theme, state, score, color in conviction_rows:
                    conviction_html += (
                        f'<div style="margin-bottom:13px;">'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                                f'<span>{theme}</span>'
                                f'<b style="color:{color};">{state}</b>'
                            f'</div>'
                            f'<div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.08); margin-top:5px; overflow:hidden;">'
                                f'<div style="width:{score}%; height:100%; background:{color}; border-radius:999px;"></div>'
                            f'</div>'
                        f'</div>'
                    )

                conviction_html += '</div>'
                st.markdown(conviction_html, unsafe_allow_html=True)

            st.markdown("### AI Desk Interpretation")

            ai_insight_read = (
                f"[Desk Read]<br>"
                f"{desk_thesis}<br><br>"

                f"[Signal Priority]<br>"
                f"Regime remains the primary support variable. Correlation compression and growth crowding remain the main portfolio fragility channels.<br><br>"

                f"[Risk Watch]<br>"
                f"Watch for volatility expansion, factor dispersion collapse, and AI-spend deceleration. Those conditions would pressure survivability before headline return deteriorates.<br><br>"

                f"[Trader Bias]<br>"
                f"Stay constructive while regime holds. Do not add beta if dispersion deteriorates."
            )

            st.markdown(
                f'<div class="portfolio-card" style="min-height:220px; padding:16px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                        f'<div style="font-size:0.78rem; color:rgba(231,238,249,0.52); letter-spacing:0.08em;">AI DESK INTERPRETATION</div>'
                        f'<div style="font-size:0.72rem; color:#2EE59D; font-weight:900;">LIVE INTELLIGENCE</div>'
                    f'</div>'
                    f'<div style="color:#E7EEF9; font-size:0.88rem; line-height:1.62;">'
                        f'{ai_insight_read}'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="portfolio-card" style="margin-top:10px; padding:10px 14px; display:flex; justify-content:center; gap:28px; '
                f'color:rgba(231,238,249,0.68); font-size:0.78rem;">'
                    f'<span style="color:#2EE59D; font-weight:950;">AI INSIGHTS LIVE</span>'
                    f'<span>Regime: {market_regime["regime"]}</span>'
                    f'<span>Vol: {ai_vol_state}</span>'
                    f'<span>Crowding: {ai_crowding_state}</span>'
                    f'<span>Desk Score: {insight_score}/100</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.stop()

        if selected_view != "Command Center":
            st.markdown(
                f'<div class="portfolio-card" style="padding:22px; margin-top:12px;">'
                    f'<div style="font-size:1.4rem; font-weight:950; color:#E7EEF9;">{selected_view}</div>'
                    f'<div style="color:rgba(231,238,249,0.62); margin-top:6px;">This deep-dive workspace stays tied to {portfolio_type}.</div>'
                    f'<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-top:18px;">'
                        f'<div class="metric-tile"><div class="metric-label">Portfolio</div><div class="metric-value">${portfolio_size:,.0f}</div></div>'
                        f'<div class="metric-tile"><div class="metric-label">Expected Return</div><div class="metric-value">{expected_return}</div></div>'
                        f'<div class="metric-tile"><div class="metric-label">Risk Level</div><div class="metric-value" style="color:{risk_color};">{risk_level}</div></div>'
                        f'<div class="metric-tile"><div class="metric-label">Status</div><div class="metric-value" style="color:#73CFFF;">Coming Soon</div></div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; margin-top:14px;">'
                    f'<div class="portfolio-card" style="min-height:180px;"><div class="engine-card-title">Primary Analysis</div><div class="portfolio-placeholder medium">Dedicated calculations and charts will live here.</div></div>'
                    f'<div class="portfolio-card" style="min-height:180px;"><div class="engine-card-title">AI Interpretation</div><div class="portfolio-placeholder medium">AI brief placeholder.</div></div>'
                    f'<div class="portfolio-card" style="min-height:180px;"><div class="engine-card-title">Portfolio Actions</div><div class="portfolio-placeholder medium">Recommendations placeholder.</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
                        
           
            

        # -----------------------------
        # Command Center top grid
        # -----------------------------
        top_left, top_mid, top_right = st.columns([2.2, 0.95, 1.35], gap="medium")

        with top_left:
            st.markdown("### 1. Suggested Portfolio vs SPY")
            if growth is not None:
                fig_growth = go.Figure()
                fig_growth.update_layout(hovermode="x unified")
                colors = {
                    "Allocation Engine": "#3A8DFF",
                    "SPY": "rgba(255,255,255,0.65)",
                    "Growth Strategy": "#2EE59D",
                    "Concentrated Alpha": "#9B5CF6",
                    "Defensive Allocation": "#F59E0B",
                }
                for col in growth.columns:
                    fig_growth.add_trace(
                        go.Scatter(
                            x=growth.index,
                            y=growth[col],
                            mode="lines",
                            name=col,
                            line=dict(color=colors.get(col, "#E7EEF9"), width=3 if col == "Allocation Engine" else 1.6),
                        )
                    )
                fig_growth.update_layout(
                    height=440,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E7EEF9"),
                    margin=dict(l=10, r=10, t=8, b=8),
                    legend=dict(orientation="h", y=1.08, x=0, font=dict(size=10, color="#FFFFFF"), bgcolor="rgba(0,0,0,0)"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Growth of $100"),
                )
                st.plotly_chart(fig_growth, use_container_width=True)
            else:
                st.info("Live performance chart will appear once market data loads.")

        with top_mid:
            st.markdown("### 2. Allocation Mix")
            fig_alloc = go.Figure(
                data=[
                    go.Pie(
                        labels=list(allocation.keys()),
                        values=list(allocation.values()),
                        hole=0.58,
                        textinfo="percent",
                        hoverinfo="label+percent",
                        domain=dict(x=[0.12, 0.88], y=[0.18, 0.88]),
                        marker=dict(colors=[bucket_colors.get(k, "#E7EEF9") for k in allocation.keys()]),
                    )
                ]
            )
            fig_alloc.update_layout(
                height=440,
                margin=dict(l=0, r=0, t=8, b=15),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E7EEF9", size=10),

                showlegend=True,

                legend=dict(
                    orientation="h",
                    y=-0.04,
                    x=0.5,
                    xanchor="center",
                    font=dict(size=9, color="#E7EEF9"),
                    bgcolor="rgba(0,0,0,0)",
                ),
            )
            st.plotly_chart(fig_alloc, use_container_width=True)

        with top_right:
            st.markdown("### 3. Capital Deployment")
            total_buy = sum(p["dollars"] for p in recommendations)
            deployed_pct = (total_buy / portfolio_size) * 100 if portfolio_size else 0
            cash_left = max(0, portfolio_size - total_buy)
            buy_rows = ""
            for pick in recommendations:
                buy_rows += (
                    f'<tr>'
                    f'<td>{pick["ticker"]}</td>'
                    f'<td>{pick["shares"]:.2f}</td>'
                    f'<td>${pick["dollars"]:,.0f}</td>'
                    f'<td style="color:{bucket_colors.get(pick["bucket"], "#E7EEF9")};">{pick["bucket"]}</td>'
                    f'</tr>'
                )
            st.markdown(
                f'<div class="portfolio-card" style="min-height:315px;">'
                    f'<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:12px;">'
                        f'<div><div class="mini-label">Starting</div><div class="mini-value">${portfolio_size:,.0f}</div></div>'
                        f'<div><div class="mini-label">Deployed</div><div class="mini-value">${total_buy:,.0f}</div></div>'
                        f'<div><div class="mini-label">Cash</div><div class="mini-value">${cash_left:,.0f}</div></div>'
                        f'<div><div class="mini-label">Deploy %</div><div class="mini-value" style="color:#2EE59D;">{deployed_pct:.1f}%</div></div>'
                    f'</div>'
                    f'<table style="width:100%; border-collapse:collapse; font-size:0.73rem; color:#E7EEF9;">'
                        f'<thead style="color:rgba(231,238,249,0.55);"><tr><th style="text-align:left;">Ticker</th><th>Shares</th><th>$</th><th>Bucket</th></tr></thead>'
                        f'<tbody>{buy_rows}</tbody>'
                    f'</table>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # -----------------------------
        # Mid row: Plan Controls + AI + deployment map
        # -----------------------------
        mid_left, mid_mid, mid_right = st.columns([0.95, 1.35, 1.35], gap="medium")

        # ---------------------------------
        # LEFT — PLAN CONTROLS
        # ---------------------------------
        with mid_left:

            st.markdown("### Plan Controls")

            with st.container():

                st.number_input(
                    "Portfolio Size ($)",
                    min_value=1000,
                    max_value=10000000,
                    step=1000,
                    value=100000,
                    key="allocation_portfolio_size"
                )

                st.markdown("**Mandate**")

                mandate_cols = st.columns(2)

                for i, mandate_option in enumerate(
                    ["Growth", "Defensive", "Absolute Return", "Opportunistic"]
                ):

                    with mandate_cols[i % 2]:

                        if st.button(
                            mandate_option,
                            key=f"allocation_mandate_{mandate_option}",
                            use_container_width=True,
                            type="primary"
                            if st.session_state.allocation_mandate == mandate_option
                            else "secondary",
                        ):

                            st.session_state.allocation_mandate = mandate_option
                            st.rerun()

                st.markdown("**Risk Budget**")

                risk_cols = st.columns(3)

                for i, risk_option in enumerate(["Low", "Medium", "High"]):

                    with risk_cols[i]:

                        if st.button(
                            risk_option,
                            key=f"allocation_risk_{risk_option}",
                            use_container_width=True,
                            type="primary"
                            if st.session_state.allocation_risk == risk_option
                            else "secondary",
                        ):

                            st.session_state.allocation_risk = risk_option
                            st.rerun()

                st.markdown("**Horizon**")

                horizon_cols = st.columns(4)

                for i, horizon in enumerate(["1Y", "3Y", "5Y", "10Y"]):

                    with horizon_cols[i]:

                        if st.button(
                            horizon,
                            key=f"allocation_horizon_{horizon}",
                            use_container_width=True,
                            type="primary"
                            if st.session_state.allocation_horizon == horizon
                            else "secondary",
                        ):

                            st.session_state.allocation_horizon = horizon
                            st.rerun()

        # ---------------------------------
        # MIDDLE — AI EXECUTIVE SUMMARY
        # ---------------------------------
        with mid_mid:

            allocation_ai_text = generate_allocation_brief(
                portfolio_type,
                risk_level,
                expected_return,
                volatility,
                drawdown,
                sharpe,
                vs_spy,
                best_strategy,
                closest,
                gap_driver,
                outperformance,
                st.session_state.allocation_horizon,
            )

            st.markdown(
                f'<div class="portfolio-card" style="min-height:245px;">'
                    f'<div class="engine-card-title">AI Executive Summary</div>'
                    f'<div style="font-size:0.82rem; line-height:1.5; color:#E7EEF9;">'
                        f'{allocation_ai_text.replace(chr(10), "<br>")}'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ---------------------------------
        # RIGHT — CAPITAL DEPLOYMENT MAP
        # ---------------------------------
        with mid_right:

            st.markdown("### 4. Capital Deployment Map")

            deployment_order = [
                "Core Beta",
                "Growth Tilt",
                "Alpha Sleeve",
                "Defensive Hedge",
                "Liquidity",
            ]

            map_html = (
                f'<div style="display:grid; '
                f'grid-template-columns:repeat(2, 1fr); gap:10px;">'
            )

            for bucket in deployment_order:

                if bucket not in allocation:
                    continue

                weight = allocation[bucket]

                dollar_value = portfolio_size * (weight / 100)

                color = bucket_colors.get(bucket, "#E7EEF9")

                map_html += (
                    f'<div class="portfolio-card" '
                    f'style="min-height:105px; '
                    f'background:linear-gradient(135deg,{color}2B,rgba(9,23,51,0.94));">'

                        f'<div style="font-size:0.70rem; '
                        f'color:rgba(231,238,249,0.75);">'
                            f'{bucket}'
                        f'</div>'

                        f'<div style="font-size:1.45rem; '
                        f'font-weight:950; color:{color}; margin-top:5px;">'
                            f'{weight}%'
                        f'</div>'

                        f'<div style="color:#E7EEF9; font-size:0.8rem;">'
                            f'${dollar_value:,.0f}'
                        f'</div>'

                        f'<div style="color:rgba(231,238,249,0.55); '
                        f'font-size:0.64rem; margin-top:5px;">'
                            f'{assets[bucket]}'
                        f'</div>'

                    f'</div>'
                )

            map_html += f'</div>'

            st.markdown(map_html, unsafe_allow_html=True)

        # -----------------------------
        # Analytical engines
        # -----------------------------
        st.markdown('<div class="engine-section-title">Analytical Engines</div>', unsafe_allow_html=True)

        engine_top = st.columns([1.65, 1.25, 0.9, 0.9], gap="medium")

        with engine_top[0]:
            st.markdown("### 5. Monte Carlo Lab")
            st.slider("Auto simulations", 100, 1500, 500, step=100, key="mc_auto_simulations")

            if mc:
                st.markdown(
                    f'<div class="portfolio-card" style="padding:10px; margin-top:8px;">'
                        f'<div style="display:grid; grid-template-columns:repeat(5,1fr); gap:8px;">'
                            f'<div><div class="mini-label">Expected</div><div class="mini-value">${mc["expected_final_value"]:,.0f}</div></div>'
                            f'<div><div class="mini-label">Median</div><div class="mini-value">${mc["median_final_value"]:,.0f}</div></div>'
                            f'<div><div class="mini-label">5% Worst</div><div class="mini-value" style="color:#FF4D6D;">${mc["worst_5_percent"]:,.0f}</div></div>'
                            f'<div><div class="mini-label">95% Best</div><div class="mini-value" style="color:#3A8DFF;">${mc["best_95_percent"]:,.0f}</div></div>'
                            f'<div><div class="mini-label">Loss Prob.</div><div class="mini-value" style="color:#2EE59D;">{mc["probability_loss"]:.1%}</div></div>'
                        f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                paths_df = pd.DataFrame(mc["paths"])
                fig_mc = go.Figure()
                sample_paths = paths_df.iloc[:, : min(55, paths_df.shape[1])]
                for col in sample_paths.columns:
                    fig_mc.add_trace(go.Scatter(y=sample_paths[col], mode="lines", line=dict(width=1, color="rgba(58,141,255,0.11)"), showlegend=False, hoverinfo="skip"))
                fig_mc.add_trace(go.Scatter(y=paths_df.median(axis=1), mode="lines", name="Median", line=dict(width=3, color="#2EE59D")))
                fig_mc.add_trace(go.Scatter(y=paths_df.quantile(0.05, axis=1), mode="lines", name="5th", line=dict(width=2.4, color="#FF4D6D")))
                fig_mc.add_trace(go.Scatter(y=paths_df.quantile(0.95, axis=1), mode="lines", name="95th", line=dict(width=2.4, color="#3A8DFF")))
                fig_mc.update_layout(
                    height=245,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E7EEF9"),
                    margin=dict(l=8, r=8, t=16, b=8),
                    legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Trading Days"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Portfolio Value"),
                )
                st.plotly_chart(fig_mc, use_container_width=True)
            else:
                st.markdown('<div class="portfolio-placeholder tall">Monte Carlo data unavailable.</div>', unsafe_allow_html=True)

        with engine_top[1]:
            st.markdown("### 6. Risk Engine")
            risk_contrib = calculate_allocation_risk_contribution(allocation, assets, st.session_state.allocation_horizon)
            risk_rows = ""
            if risk_contrib:
                for name, value in sorted(risk_contrib.items(), key=lambda x: x[1], reverse=True):
                    color = bucket_colors.get(name, "#E7EEF9")
                    risk_rows += (
                        f'<div style="margin-top:8px;">'
                            f'<div style="display:flex; justify-content:space-between; font-size:0.76rem;"><span>{name}</span><span>{value:.1f}%</span></div>'
                            f'<div style="height:7px; border-radius:6px; background:rgba(255,255,255,0.08); margin-top:4px;"><div style="width:{value}%; height:100%; border-radius:6px; background:{color};"></div></div>'
                        f'</div>'
                    )
            st.markdown(
                f'<div class="portfolio-card" style="min-height:352px;">'
                    f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">'
                        f'<div><div class="engine-card-title">Risk Contribution</div>{risk_rows}</div>'
                        f'<div><div class="engine-card-title">Key Risk Metrics</div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Volatility</span><span style="color:#2EE59D;">{volatility}</span></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Max Drawdown</span><span style="color:#FF4D6D;">{drawdown}</span></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Sharpe</span><span>{sharpe}</span></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Beta vs SPY</span><span>0.92</span></div>'
                            f'<div style="display:flex; justify-content:space-between;"><span>Corr. vs SPY</span><span style="color:#2EE59D;">0.88</span></div>'
                        f'</div>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with engine_top[2]:
            st.markdown("### 7. Stress Test")
            stress = [("Recession", "-24.6%", "#FF4D6D"), ("Inflation Spike", "-18.3%", "#FF4D6D"), ("Tech Selloff", "-28.7%", "#FF4D6D"), ("Rates Shock", "-16.2%", "#FF4D6D"), ("Credit Crunch", "-31.4%", "#FF4D6D"), ("Bull Market", "+21.8%", "#2EE59D")]
            stress_rows = "".join([f'<tr><td style="padding:7px;">{n}</td><td style="padding:7px; color:{c}; font-weight:900; text-align:right;">{v}</td></tr>' for n, v, c in stress])
            st.markdown(f'<div class="portfolio-card" style="min-height:352px;"><table style="width:100%; border-collapse:collapse; font-size:0.8rem;"><thead style="color:rgba(231,238,249,0.55);"><tr><th style="text-align:left;">Scenario</th><th style="text-align:right;">Impact</th></tr></thead><tbody>{stress_rows}</tbody></table></div>', unsafe_allow_html=True)

        with engine_top[3]:
            st.markdown("### 8. Factor Exposure")
            factors = [("Market", 0.92), ("Size", 0.15), ("Value", 0.22), ("Momentum", 0.35), ("Quality", 0.48), ("Low Vol", 0.88), ("Growth", 0.62)]
            factor_rows = "".join([f'<div style="display:flex; justify-content:space-between; margin-top:10px; font-size:0.82rem;"><span>{n}</span><span>{v:.2f}</span></div>' for n, v in factors])
            st.markdown(f'<div class="portfolio-card" style="min-height:352px;"><div style="display:flex; justify-content:space-between; color:rgba(231,238,249,0.55); font-size:0.74rem;"><span>Factor</span><span>Exposure</span></div>{factor_rows}</div>', unsafe_allow_html=True)

        engine_bottom = st.columns([1.05, 1.05, 1.1, 1.15, 0.95], gap="medium")

        with engine_bottom[0]:
            st.markdown("### 9. Correlation")

            corr = calculate_allocation_correlation_matrix(
                recommendations,
                st.session_state.allocation_horizon
            )

            if corr is not None:
                fig_corr = go.Figure(
                    data=go.Heatmap(
                        z=corr.values,
                        x=corr.columns,
                        y=corr.index,
                        zmin=-1,
                        zmax=1,
                        colorscale=[
                            [0.0, "#FF4D6D"],
                            [0.5, "#091733"],
                            [1.0, "#2EE59D"],
                        ],
                        colorbar=dict(
                            title=dict(
                                text="Corr",
                                font=dict(color="#E7EEF9")
                            ),
                            tickfont=dict(color="#E7EEF9"),
                        ),
                    )
                )

                fig_corr.update_layout(
                    height=185,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E7EEF9", size=10),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False),
                )
                avg_corr = corr.where(~np.eye(corr.shape[0], dtype=bool)).stack().mean()
                corr_box = st.container(border=True)

                with corr_box:
                    st.plotly_chart(fig_corr, use_container_width=True)

                    st.markdown(
                        f"""
                        <div class="engine-card-body" style="margin-top:-8px;">
                            Avg correlation: <b>{avg_corr:.2f}</b><br>
                            Detects hidden overlap and fake diversification.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(
                    '<div class="portfolio-card" style="min-height:238px;">'
                    '<div class="portfolio-placeholder medium">Correlation data unavailable.</div>'
                    '<div class="engine-card-body" style="margin-top:10px;">Detects hidden overlap and fake diversification.</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
        with engine_bottom[1]:
            st.markdown("### 10. Scenario")
            st.markdown(f'<div class="portfolio-card" style="min-height:238px;"><div class="engine-card-title">Custom Scenario Builder</div><div style="display:grid; gap:7px;"><div style="display:flex; justify-content:space-between;"><span>GDP Growth</span><span>-1.0%</span></div><div style="display:flex; justify-content:space-between;"><span>Inflation</span><span>+2.5%</span></div><div style="display:flex; justify-content:space-between;"><span>Rates</span><span>+1.0%</span></div><div style="display:flex; justify-content:space-between;"><span>Equities</span><span>-15.0%</span></div></div><div style="margin-top:14px; color:#FF4D6D; font-size:1.15rem; font-weight:950;">Impact: -19.7%</div></div>', unsafe_allow_html=True)

        with engine_bottom[2]:
            st.markdown("### 11. AI Insights")
            st.markdown(f'<div class="portfolio-card" style="min-height:238px;"><div style="line-height:1.75; font-size:0.82rem;">🟣 Long-term growth drivers<br>🟠 Moderate tech concentration<br>🟢 Good asset-class diversification<br>🔵 Recession/credit sensitivity<br>🔵 Watch volatility regime shifts</div></div>', unsafe_allow_html=True)

        with engine_bottom[3]:
            st.markdown("### 12. Market Regime")
            st.markdown(
                f'<div class="portfolio-card" style="min-height:238px;">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<div class="mini-label">MARKET REGIME</div>'
                        f'<div style="width:8px; height:8px; border-radius:50%; background:{market_regime["color"]}; box-shadow:0 0 12px {market_regime["color"]};"></div>'
                    f'</div>'
                    f'<div style="margin-top:10px; padding:10px; border-radius:14px; background:linear-gradient(135deg, rgba(46,229,157,0.08), rgba(58,141,255,0.03)); border:1px solid {market_regime["color"]};">'
                        f'<div style="color:{market_regime["color"]}; font-size:1.05rem; font-weight:800;">{market_regime["regime"]}</div>'
                    f'</div>'
                    f'<div style="margin-top:12px; display:flex; justify-content:space-between; font-size:0.78rem;">'
                        f'<span>Risk-On</span><span>{market_regime["probabilities"]["Risk-On"]:.0f}%</span>'
                    f'</div>'
                    f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                        f'<span>Late Cycle</span><span>{market_regime["probabilities"]["Late Cycle"]:.0f}%</span>'
                    f'</div>'
                    f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                        f'<span>Risk-Off</span><span>{market_regime["probabilities"]["Risk-Off"]:.0f}%</span>'
                    f'</div>'
                    f'<div style="display:flex; justify-content:space-between; font-size:0.78rem;">'
                        f'<span>Recession</span><span>{market_regime["probabilities"]["Recession"]:.0f}%</span>'
                    f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        

        with engine_bottom[4]:
            st.markdown("### Health")
            st.markdown(f'<div class="portfolio-card" style="min-height:238px; text-align:center;"><div style="margin:10px auto; width:112px; height:112px; border-radius:50%; background:conic-gradient(#2EE59D 0deg, #2EE59D 295deg, rgba(255,255,255,0.08) 295deg); display:flex; align-items:center; justify-content:center;"><div style="width:78px; height:78px; border-radius:50%; background:#091733; display:flex; align-items:center; justify-content:center; flex-direction:column;"><div style="font-size:1.8rem; font-weight:950;">82</div><div style="font-size:0.65rem;">/100</div></div></div><div style="color:#2EE59D; font-size:1rem; font-weight:900;">Good</div></div>', unsafe_allow_html=True)

        st.markdown(
            """
            <div style="margin-top:18px; text-align:center; color:rgba(231,238,249,0.48); font-size:0.78rem;">
                This tool is for educational and informational purposes only and does not constitute investment advice.
            </div>
            """,
            unsafe_allow_html=True,
        )
