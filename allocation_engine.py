import pandas as pd
import numpy as np
import yfinance as yf
import requests
import certifi
from io import StringIO
from database import get_engine

# -----------------------------
# 1. Define Universe
# -----------------------------

def get_market_universe():
    """
    Live universe:
    - S&P 500 from Wikipedia
    - Nasdaq 100 from Wikipedia
    - Dow 30 from Wikipedia

    Uses requests + certifi to avoid Mac SSL certificate errors.
    """

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    def read_live_table(url):
        response = requests.get(
            url,
            headers=headers,
            verify=certifi.where(),
            timeout=20
        )
        response.raise_for_status()
        return pd.read_html(StringIO(response.text))

    sp500_df = pd.read_csv("data/sp500.csv")
    sp500 = sp500_df["Ticker"].tolist()

    
    

    nasdaq_tables = read_live_table(
    "https://en.wikipedia.org/wiki/Nasdaq-100"
    )

    nasdaq100 = None

    for table in nasdaq_tables:
        cols = [str(c) for c in table.columns]

        if "Ticker" in cols:
            nasdaq100 = table["Ticker"]
            break

        if "Symbol" in cols:
            nasdaq100 = table["Symbol"]
            break

    if nasdaq100 is None:
        raise ValueError("Could not find Nasdaq ticker column")
    
    

    dow_tables = read_live_table(
    "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
    )

    dow30 = None

    for table in dow_tables:
        cols = [str(c) for c in table.columns]

        if "Symbol" in cols:
            dow30 = table["Symbol"]
            break

        if "Ticker" in cols:
            dow30 = table["Ticker"]
            break

    if dow30 is None:
        raise ValueError("Could not find Dow ticker column")

   

    sp500 = pd.read_csv("data/sp500.csv")["Ticker"].tolist()
    nasdaq100 = pd.read_csv("data/nasdaq100.csv")["Ticker"].tolist()
    dow30 = pd.read_csv("data/dow30.csv")["Ticker"].tolist()

    sp500 = pd.DataFrame({"Symbol": sp500})
    nasdaq100 = pd.DataFrame({"Symbol": nasdaq100})
    dow30 = pd.DataFrame({"Symbol": dow30})

    universe = pd.concat(
        [sp500, nasdaq100, dow30],
        ignore_index=True
    )

    universe = (
        universe["Symbol"]
        .dropna()
        .astype(str)
        .str.replace(".", "-", regex=False)
        .drop_duplicates()
        .tolist()
    )

    return universe

# -----------------------------
# 2. Collect Live Market Data
# -----------------------------

def fetch_price_data(tickers, period="1y"):
    """
    Pull adjusted close prices for all tickers.
    """

    data = yf.download(
        tickers,
        period=period,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True
    )

    prices = {}

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                close = data["Close"]
            else:
                close = data[ticker]["Close"]

            if close.dropna().shape[0] > 100:
                prices[ticker] = close.dropna()

        except Exception:
            continue

    return pd.DataFrame(prices)


# -----------------------------
# 3. Score Stocks
# -----------------------------

def score_stocks(price_df):
    """
    Scores stocks using:
    - 12 month momentum
    - 6 month momentum
    - volatility
    - drawdown
    - recent trend
    """

    results = []

    for ticker in price_df.columns:
        prices = price_df[ticker].dropna()

        if len(prices) < 120:
            continue

        returns = prices.pct_change().dropna()

        momentum_12m = (prices.iloc[-1] / prices.iloc[0]) - 1
        momentum_6m = (prices.iloc[-1] / prices.iloc[-126]) - 1 if len(prices) >= 126 else momentum_12m
        volatility = returns.std() * np.sqrt(252)

        rolling_high = prices.cummax()
        drawdown = ((prices / rolling_high) - 1).min()

        sma_50 = prices.rolling(50).mean().iloc[-1]
        sma_200 = prices.rolling(200).mean().iloc[-1] if len(prices) >= 200 else prices.mean()

        trend_score = 1 if sma_50 > sma_200 else 0

        results.append({
            "Ticker": ticker,
            "Momentum_12M": momentum_12m,
            "Momentum_6M": momentum_6m,
            "Volatility": volatility,
            "Max_Drawdown": drawdown,
            "Trend_Score": trend_score,
        })

    df = pd.DataFrame(results)

    if df.empty:
        return df

    # Normalize factors
    df["Momentum_12M_Rank"] = df["Momentum_12M"].rank(pct=True)
    df["Momentum_6M_Rank"] = df["Momentum_6M"].rank(pct=True)
    df["Low_Vol_Rank"] = (1 - df["Volatility"].rank(pct=True))
    df["Drawdown_Rank"] = df["Max_Drawdown"].rank(pct=True)

    df["AInvest_Score"] = (
        df["Momentum_12M_Rank"] * 0.30 +
        df["Momentum_6M_Rank"] * 0.25 +
        df["Low_Vol_Rank"] * 0.20 +
        df["Drawdown_Rank"] * 0.15 +
        df["Trend_Score"] * 0.10
    ) * 100

    return df.sort_values("AInvest_Score", ascending=False)


# -----------------------------
# 4. Rank Candidates
# -----------------------------


def get_ranked_candidates(risk_budget="Medium", top_n=25):
    """
    Fast path:
    Reads precomputed rankings from Render Postgres.
    """

    engine = get_engine()

    ranked = pd.read_sql(
        "SELECT * FROM ranked_candidates",
        engine
    )

    if ranked.empty:
        return ranked

    if risk_budget == "Low":
        ranked = ranked.sort_values(
            ["Low_Vol_Rank", "AInvest_Score"],
            ascending=False
        )

    elif risk_budget == "High":
        ranked = ranked.sort_values(
            ["Momentum_6M_Rank", "Momentum_12M_Rank", "AInvest_Score"],
            ascending=False
        )

    else:
        ranked = ranked.sort_values("AInvest_Score", ascending=False)

    return ranked.head(top_n)

# -----------------------------
# 5. Build Portfolio
# -----------------------------

def build_portfolio(starting_capital, risk_budget="Medium", top_n=10):
    """
    Builds portfolio using score-weighted allocation.
    """

    ranked = get_ranked_candidates(risk_budget=risk_budget, top_n=25)

    if ranked.empty:
        return pd.DataFrame(), ranked

    selected = ranked.head(top_n).copy()

    # Risk-adjusted weight: score divided by volatility
    selected["Raw_Weight"] = selected["AInvest_Score"] / selected["Volatility"]

    selected["Weight"] = selected["Raw_Weight"] / selected["Raw_Weight"].sum()

    selected = apply_risk_controls(selected, risk_budget)

    selected["Allocation"] = selected["Weight"] * starting_capital

    return selected, ranked


# -----------------------------
# 6. Apply Risk Controls
# -----------------------------

def apply_risk_controls(portfolio_df, risk_budget):
    """
    Caps position sizes based on risk level.
    """

    df = portfolio_df.copy()

    if risk_budget == "Low":
        max_position = 0.12
    elif risk_budget == "High":
        max_position = 0.20
    else:
        max_position = 0.15

    df["Weight"] = df["Weight"].clip(upper=max_position)

    # Re-normalize after caps
    df["Weight"] = df["Weight"] / df["Weight"].sum()

    return df


# -----------------------------
# 7. Generate AI Thesis Helper
# -----------------------------

def create_portfolio_summary(portfolio_df, risk_budget):
    """
    Creates a clean text summary that can be sent to OpenAI.
    """

    tickers = ", ".join(portfolio_df["Ticker"].tolist())

    top_names = portfolio_df.sort_values("Weight", ascending=False).head(5)

    summary = f"""
    Risk Budget: {risk_budget}

    Selected Portfolio:
    {tickers}

    Top Allocations:
    {top_names[["Ticker", "Weight", "AInvest_Score", "Volatility"]].to_string(index=False)}

    The portfolio was selected using live market data, momentum, volatility,
    drawdown control, and trend strength.
    """

    return summary