# AInvest 📈

AI-powered stock analysis dashboard built with Streamlit, OpenAI, and live market data.

## Live App
Add your Render link here after deployment.

## Overview
AInvest is an interactive market dashboard that ranks a live watchlist of stocks, identifies the current top model pick, and uses AI to explain why that stock ranks highest right now.

The app combines:
- live market data from yfinance
- momentum-based ranking logic
- AI-generated market commentary
- a clean trading-dashboard interface

## Features
- **Top Model Pick** hero card with live ranking
- **Live Watchlist Ranking** table across major stocks
- **AI Market Insight** explaining why the top stock ranks first
- **Analyze a Stock** tool for ticker-level analysis
- confidence, risk, daily change, and trend-vs-MA20 metrics
- recent headlines for context

## Tech Stack
- Python
- Streamlit
- OpenAI API
- yfinance
- pandas

## How It Works
### 1. Live ranking engine
The app pulls recent price history for a watchlist of stocks and scores each one using short-term momentum and trend signals.

### 2. Top pick selection
The highest-ranked stock becomes the **Top Model Pick** shown at the top of the dashboard.

### 3. AI explanation layer
OpenAI generates a plain-English explanation for why the stock may be ranked highest, using:
- ticker
- confidence
- risk
- recent price move
- recent headlines

### 4. Drill-down analysis
Users can type in a ticker to view:
- signal
- confidence
- risk
- latest price
- daily change
- chart
- AI explanation
- recent headlines

## Example Watchlist
The current live watchlist includes:
- AAPL
- MSFT
- NVDA
- AMZN
- TSLA
- META
- GOOGL
- F
- GM

## Run Locally
Install dependencies:

```bash
pip install -r requirements.txt