import os
import streamlit as st
import pandas as pd
import yfinance as yf
from openai import OpenAI

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="AInvest",
    layout="centered",
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
# Styling
# -----------------------------
st.markdown("""
<style>
body {
    background: #0b1220;
    color: #e5e7eb;
}

.main {
    background: #0b1220;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

h1, h2, h3 {
    color: #f8fafc;
    margin-bottom: 0.35rem;
}

.center {
    text-align: center;
}

.small-text {
    color: #94a3b8;
    font-size: 0.92rem;
}

.dashboard-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #f8fafc;
    text-align: center;
    margin-bottom: 0.25rem;
}

.dashboard-subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 1.75rem;
}

.card {
    background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
    border: 1px solid #1f2937;
    padding: 1.35rem;
    border-radius: 18px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.28);
    margin-bottom: 1rem;
    color: #e5e7eb;
}

.hero-card {
    background: linear-gradient(135deg, #111827 0%, #172554 100%);
    border: 1px solid #334155;
    padding: 1.75rem;
    border-radius: 22px;
    box-shadow: 0 14px 36px rgba(0,0,0,0.35);
    margin-bottom: 1.25rem;
    color: #f8fafc;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.85rem;
    margin-top: 1rem;
}

.metric-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 0.9rem;
}

.metric-label {
    color: #94a3b8;
    font-size: 0.82rem;
    margin-bottom: 0.25rem;
}

.metric-value {
    color: #f8fafc;
    font-size: 1.1rem;
    font-weight: 700;
}

.ai-box {
    background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
    border: 1px solid #1f2937;
    border-left: 4px solid #8b5cf6;
    padding: 1.15rem 1.25rem;
    border-radius: 18px;
    margin-top: 0.75rem;
    margin-bottom: 1rem;
    box-shadow: 0 12px 30px rgba(0,0,0,0.22);
    color: #e5e7eb;
    line-height: 1.65;
}

.news-box {
    background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
    border: 1px solid #1f2937;
    padding: 1.15rem 1.25rem;
    border-radius: 18px;
    margin-top: 0.75rem;
    margin-bottom: 1rem;
    box-shadow: 0 12px 30px rgba(0,0,0,0.22);
    color: #e5e7eb;
}

.section-title {
    color: #f8fafc;
    font-size: 1.5rem;
    font-weight: 800;
    margin-top: 1rem;
    margin-bottom: 0.75rem;
}

.signal-pill {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.03em;
}

.buy-pill {
    background: rgba(34,197,94,0.16);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,0.35);
}

.hold-pill {
    background: rgba(245,158,11,0.16);
    color: #fbbf24;
    border: 1px solid rgba(245,158,11,0.35);
}

.sell-pill {
    background: rgba(239,68,68,0.16);
    color: #f87171;
    border: 1px solid rgba(239,68,68,0.35);
}

hr {
    border: none;
    border-top: 1px solid #1f2937;
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)

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

@st.cache_data(ttl=900, show_spinner=False)
def build_live_watchlist_ranking(watchlist: list[str]) -> pd.DataFrame:
    rows = []

    for ticker in watchlist:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")

            if hist.empty or len(hist) < 20:
                continue

            latest_close = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2])
            ma20 = float(hist["Close"].rolling(20).mean().iloc[-1])

            daily_change_pct = ((latest_close - prev_close) / prev_close) * 100 if prev_close else 0.0
            vs_ma20_pct = ((latest_close - ma20) / ma20) * 100 if ma20 else 0.0

            # Simple scoring model
            score = 50.0

            # Daily momentum
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

            # Trend vs MA20
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

            score = max(1.0, min(99.0, round(score, 2)))

            rows.append({
                "Ticker": ticker,
                "Up Probability": score / 100.0,
                "Latest Price": round(latest_close, 2),
                "Daily Change %": round(daily_change_pct, 2),
                "Vs MA20 %": round(vs_ma20_pct, 2),
            })

        except Exception:
            continue

    if not rows:
        return pd.DataFrame(columns=[
            "Ticker", "Up Probability", "Latest Price", "Daily Change %", "Vs MA20 %"
        ])

    return pd.DataFrame(rows).sort_values("Up Probability", ascending=False).reset_index(drop=True)

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


def get_signal(confidence: float):
    if confidence >= 70:
        return "BUY", "green"
    if confidence >= 50:
        return "HOLD", "orange"
    return "SELL", "red"


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

        for item in raw_news[:5]:
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
# AI helper
# -----------------------------
@st.cache_data(show_spinner=False, ttl=300)
def generate_ai_explanation(
    ticker: str,
    confidence: float,
    risk: str,
    source_used: str,
    latest_price: float | None = None,
    daily_change: float | None = None,
    headlines: tuple[str, ...] = (),
) -> str:
    if not api_key or client is None:
        return "AI explanation unavailable because OPENAI_API_KEY is not set."

    price_text = f"${latest_price:.2f}" if latest_price is not None else "N/A"
    change_text = f"${daily_change:.2f}" if daily_change is not None else "N/A"

    if headlines:
        headline_block = "\n".join([f"- {h}" for h in headlines])
    else:
        headline_block = "No recent headlines available."

    prompt = f"""
You are an AI financial assistant inside a stock analysis app.

Write a concise explanation in 3 to 4 sentences.

Rules:
- Use only the inputs provided
- Do not invent facts
- Do not overstate causation
- If headlines are only loosely related, say they may provide context but do not clearly explain today's move
- Do not give buy or sell advice

Focus on:
- What today's price move suggests
- Whether momentum looks strong, weak, or neutral
- Whether the headlines clearly support the move or not

Inputs:
Ticker: {ticker}
Confidence: {confidence:.2f}%
Risk: {risk}
Source used: {source_used}
Latest price: {price_text}
Daily change: {change_text}

Recent headlines:
{headline_block}
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        text = (response.output_text or "").strip()
        return text if text else "AI explanation unavailable right now."
    except Exception:
        return "AI explanation unavailable right now."

# -----------------------------
# Load data
# -----------------------------
df = load_top_signals()

watchlist = ["AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "META", "GOOGL", "F", "GM"]
live_rank_df = build_live_watchlist_ranking(watchlist)

# -----------------------------
# App header
# -----------------------------
if not live_rank_df.empty:
    top_stock = live_rank_df.iloc[0]
    top_ticker = top_stock["Ticker"]
    top_confidence = round(float(top_stock["Up Probability"]) * 100, 2)
    top_price = top_stock["Latest Price"]
    top_daily_change_pct = top_stock["Daily Change %"]
    top_vs_ma20_pct = top_stock["Vs MA20 %"]
    top_source_label = "Live watchlist ranking"
else:
    top_stock = df.iloc[0]
    top_ticker = top_stock["Ticker"]
    top_confidence = round(float(top_stock["Up Probability"]) * 100, 2)
    top_price = None
    top_daily_change_pct = None
    top_vs_ma20_pct = None
    top_source_label = "Fallback model CSV"

top_signal, _ = get_signal(top_confidence)

if top_signal == "BUY":
    top_signal_class = "signal-pill buy-pill"
elif top_signal == "HOLD":
    top_signal_class = "signal-pill hold-pill"
else:
    top_signal_class = "signal-pill sell-pill"

top_extra_html = ""

if top_price is not None:
    top_extra_html += f"""
<div class="metric-box">
    <div class="metric-label">Latest Price</div>
    <div class="metric-value">${top_price}</div>
</div>
"""

if top_daily_change_pct is not None:
    top_extra_html += f"""
<div class="metric-box">
    <div class="metric-label">Daily Change</div>
    <div class="metric-value">{top_daily_change_pct}%</div>
</div>
"""

if top_vs_ma20_pct is not None:
    top_extra_html += f"""
<div class="metric-box">
    <div class="metric-label">Vs MA20</div>
    <div class="metric-value">{top_vs_ma20_pct}%</div>
</div>
"""

st.markdown("<div class='dashboard-title'>AInvest</div>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>AI-Powered Market Intelligence Dashboard</div>", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero-card center">
    <div style="font-size:0.9rem; color:#93c5fd; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;">
        Top Model Pick
    </div>
    <h1 style="margin-top:0.45rem; margin-bottom:0.65rem;">{top_ticker}</h1>
    <div>
        <span class="{top_signal_class}">{top_signal}</span>
    </div>
    <div class="metric-grid">
        <div class="metric-box">
            <div class="metric-label">Confidence</div>
            <div class="metric-value">{top_confidence}%</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">Risk</div>
            <div class="metric-value">{get_model_risk(top_confidence)}</div>
        </div>
{top_extra_html.strip()}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    f"<div class='small-text center' style='margin-top:-0.25rem; margin-bottom:1rem;'>Source: {top_source_label}</div>",
    unsafe_allow_html=True,
)

st.markdown("### 🧠 Why This Stock?")

top_ai_summary = generate_ai_explanation(
    ticker=top_ticker,
    confidence=top_confidence,
    risk=get_model_risk(top_confidence),
    source_used=top_source_label,
    latest_price=top_price,
    daily_change=top_daily_change_pct,
    headlines=tuple(fetch_recent_headlines(top_ticker)),
)

st.markdown(f"""
<div class="ai-box">
    <b>AI Insight</b>
    <p>{top_ai_summary}</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Analyze a stock
# -----------------------------
st.markdown("### Analyze a Stock")

ticker_input = st.text_input("Enter stock symbol (e.g., AAPL)").strip().upper()
analyze_clicked = st.button("Analyze")

if analyze_clicked:
    if not ticker_input:
        st.warning("Please enter a stock symbol.")
    else:
        match = df[df["Ticker"] == ticker_input]

        # -------------------------
        # Case 1: in model CSV
        # -------------------------
        if not match.empty:
            stock_row = match.iloc[0]
            confidence = round(float(stock_row["Up Probability"]) * 100, 2)
            risk = get_model_risk(confidence)
            signal, color = get_signal(confidence)

            latest_price = None
            daily_change = None
            hist = pd.DataFrame()
            headlines = []

            try:
                stock = yf.Ticker(ticker_input)
                hist = stock.history(period="1mo")

                if not hist.empty and len(hist) >= 2:
                    latest_price = round(float(hist["Close"].iloc[-1]), 2)
                    previous_close = round(float(hist["Close"].iloc[-2]), 2)
                    daily_change = round(latest_price - previous_close, 2)

                headlines = fetch_recent_headlines(ticker_input)
            except Exception:
                pass

            ai_text = generate_ai_explanation(
                ticker=ticker_input,
                confidence=confidence,
                risk=risk,
                source_used="Model signal from top_signals.csv plus recent market headlines",
                latest_price=latest_price,
                daily_change=daily_change,
                headlines=tuple(headlines),
            )

            latest_price_html = (
                f"<p><b>Latest Price:</b> ${latest_price:.2f}</p>"
                if latest_price is not None else ""
            )
            daily_change_html = (
                f"<p><b>Daily Change:</b> ${daily_change:.2f}</p>"
                if daily_change is not None else ""
            )

            st.markdown(f"""
            <div class="card">
                <h3>{ticker_input}</h3>
                <p><b>Signal:</b> <span style="color:{color};">{signal}</span></p>
                <p><b>Confidence:</b> {confidence}%</p>
                <p><b>Risk:</b> {risk}</p>
                {latest_price_html}
                {daily_change_html}
                <p><b>Source:</b> Model signal</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### 🧠 Market Insight")

            st.markdown(f"""
            <div class="ai-box">
                <b>AI Market Insight</b>
                <p>{ai_text}</p>
            </div>
            """, unsafe_allow_html=True)

            if headlines:
                news_html = "".join([f"<li>{h}</li>" for h in headlines])
                st.markdown(f"""
                <div class="news-box">
                    <b>Recent Headlines</b>
                    <ul>{news_html}</ul>
                </div>
                """, unsafe_allow_html=True)

            if not hist.empty:
                hist["MA20"] = hist["Close"].rolling(20).mean()
                st.subheader("Price Chart (Last Month)")
                st.line_chart(hist[["Close", "MA20"]])

        # -------------------------
        # Case 2: yfinance fallback
        # -------------------------
        else:
            try:
                stock = yf.Ticker(ticker_input)
                hist = stock.history(period="1mo")

                if hist.empty or len(hist) < 2:
                    raise ValueError("No market data found for this ticker.")

                latest_price = round(float(hist["Close"].iloc[-1]), 2)
                prev_price = round(float(hist["Close"].iloc[-2]), 2)
                daily_change = round(latest_price - prev_price, 2)

                confidence = 50.0
                if daily_change > 0:
                    confidence = 55.0
                elif daily_change < 0:
                    confidence = 45.0

                risk = get_fallback_risk(confidence)
                signal, color = get_signal(confidence)
                headlines = fetch_recent_headlines(ticker_input)

                ai_text = generate_ai_explanation(
                    ticker=ticker_input,
                    confidence=confidence,
                    risk=risk,
                    source_used="yfinance fallback using recent price momentum and headlines",
                    latest_price=latest_price,
                    daily_change=daily_change,
                    headlines=tuple(headlines),
                )

                st.markdown(f"""
                <div class="card">
                    <h3>{ticker_input}</h3>
                    <p><b>Signal:</b> <span style="color:{color};">{signal}</span></p>
                    <p><b>Confidence:</b> {confidence}%</p>
                    <p><b>Risk:</b> {risk}</p>
                    <p><b>Latest Price:</b> ${latest_price}</p>
                    <p><b>Daily Change:</b> ${daily_change}</p>
                    <p><b>Source:</b> Live fallback data</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### 🧠 Market Insight")

                st.markdown(f"""
                <div class="ai-box">
                    <b>AI Market Insight</b>
                    <p>{ai_text}</p>
                </div>
                """, unsafe_allow_html=True)

                if headlines:
                    news_html = "".join([f"<li>{h}</li>" for h in headlines])
                    st.markdown(f"""
                    <div class="news-box">
                        <b>Recent Headlines</b>
                        <ul>{news_html}</ul>
                    </div>
                    """, unsafe_allow_html=True)

                hist["MA20"] = hist["Close"].rolling(20).mean()
                st.subheader("Price Chart (Last Month)")
                st.line_chart(hist[["Close", "MA20"]])

            except Exception:
                st.markdown(f"""
                <div class="card">
                    <h3>{ticker_input}</h3>
                    <p>Unable to fetch data for this ticker.</p>
                </div>
                """, unsafe_allow_html=True)

# -----------------------------
# Disclaimer
# -----------------------------
st.markdown(f"""
<p class='small-text center'>
This tool is for informational purposes only and not financial advice.
</p>
""", unsafe_allow_html=True)