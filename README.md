
# 🚀 AInvest

AI-powered investment intelligence platform that transforms raw financial data into structured signals, portfolio strategy, and capital allocation insight.

Built to simulate how modern institutional fintech systems combine quantitative models, portfolio analytics, and AI reasoning into a unified decision layer.

---

## 🌐 Live App
👉 https://ainvest-8zkq.onrender.com/

---

## 🖼 System Preview

![AInvest Preview](assets/Preview.png)

---

## 🔍 Stock Lens
[![Stock Lens](assets/page%202.png)](assets/page%202.png)

---

## 📊 Portfolio Lab
[![Portfolio Lab](assets/page3.png)](assets/page3.png)

---
## ⚙️ Allocation Engine

![Allocation Engine Preview](assets/page4.png)

## ⚡ What This Is

Most retail tools show charts.

AInvest explains decisions.

It sits between:

- raw market data  
- quantitative signals  
- AI interpretation  

and outputs a clear, decision-ready view of the market.

---

## 🧩 Core Features

### 🔍 Stock Lens
Single-ticker analysis engine:

- Signal (Bullish / Neutral / Bearish)
- Conviction score
- Risk level
- AI trader-style insight
- Real-time price + structure

---

## ⚙️ Allocation Engine (NEW)
Institutional-style capital allocation system:

Dynamic portfolio construction based on:
- mandate (growth, defensive, opportunistic)
- risk budget
- time horizon

Automatically builds:
- capital deployment plan (what to buy, how much)
- allocation map across strategy buckets
- projected performance vs SPY
- benchmark comparison vs:
  - Growth Strategy
  - Concentrated Alpha
  - Defensive Allocation

Advanced analytics:
- risk contribution breakdown by bucket
- stress testing across macro scenarios
- projected capital growth + edge vs market

Includes:
- AI allocation brief (PM-style decision note)
- live price-based position sizing
- portfolio-level performance simulation

👉 This transforms AInvest from analysis → full portfolio construction engine.

---

### 📊 Portfolio Lab (NEW)
Multi-asset portfolio analysis system:

- Add multiple tickers dynamically
- Equal weight or custom weighting
- Portfolio-level metrics:
  - Return
  - Volatility
  - Sharpe
  - Max drawdown
- Benchmark comparison (SPY + strategies)
- Stress scenario simulation
- AI portfolio brief (PM-style insight)

👉 This is the foundation for portfolio intelligence tooling, not just stock analysis.

---

## 🧠 System Architecture

AInvest runs as a layered decision pipeline:

### 1. Signal Layer
- Generates directional bias (buy / hold / sell style)
- Outputs conviction score
- Mimics lightweight quant signals

### 2. Data Layer
- Real-time market data (yfinance)
- Fallback handling for reliability
- Prevents UI/data failures

### 3. Reasoning Layer (AI)
LLM interprets:
- signals  
- price action  
- context  

Outputs:
- bias  
- conviction  
- structural narrative  

→ Converts raw data into human-readable intelligence

### 4. Presentation Layer
- Streamlit UI
- Decision-first layout
- Clean, institutional-style interface

---

## 🔁 End-to-End Flow

1. User inputs ticker(s)  
2. Signal engine evaluates position  
3. Market data is retrieved  
4. AI generates context + reasoning  
5. Unified output is displayed  

---

## ✨ Capabilities

- 📊 Quant-style signal generation  
- 🧠 AI interpretation layer  
- 📉 Portfolio analytics + benchmarking  
- ⚡ Real-time processing  
- 🛡 Resilient data handling  

---

## 🛠 Tech Stack

- Python
- Streamlit
- Pandas / NumPy
- yfinance
- OpenAI API
- Plotly

---

## 🛡️ Security & Reliability

- API keys are stored securely using Streamlit secrets / environment variables
- No API keys or secrets are hardcoded in the codebase
- Basic request rate limiting helps prevent rapid API abuse
- OpenAI spend alerts are configured to monitor usage
- External API calls use defensive error handling to prevent app crashes
- Market data fallback logic helps keep the UI stable during data issues

## 🚀 Running Locally

bash git clone https://github.com/dane-anderson/ainvest.git cd ainvest pip install -r requirements.txt streamlit run app.py 

Create a .streamlit/secrets.toml:

toml OPENAI_API_KEY = "your-key-here" 

---

## 🚀 Deployment

Deployed on Render:

- Auto-deploy from GitHub
- Python web service
- Streamlit app entry: app.py

---

## ⚠️ Design Philosophy

AInvest is not built to predict markets.

It is built to:

> structure uncertainty into interpretable signals.

---

## 🔮 Future Expansion

- Portfolio optimization engine (Allocation Engine)
- Multi-timeframe signal aggregation
- Risk modeling (beta, factor exposure)
- AI agents for automated analysis

---

## 💡 Vision

AInvest represents a shift from:

> dashboards → decision systems

The goal is to build tools that:

- ingest complex financial data  
- reason over it  
- output clear, actionable insight  

similar to internal tools used at quantitative firms.

---

## ⚠️ Disclaimer

For educational purposes only. Not financial advice
