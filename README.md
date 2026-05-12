
# 🚀 AInvest

Institutional-style financial intelligence and portfolio decision platform built to simulate how modern quantitative firms structure market signals, macro regimes, portfolio construction, and probabilistic risk analysis into a unified investment workflow.

AInvest combines quantitative analytics, simulation systems, AI reasoning, and real-time market data into an integrated decision engine.

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

Most retail platforms show charts.

AInvest builds decision systems.

It sits between:

- real-time market data  
- quantitative signals  
- macro regime analysis  
- portfolio construction  
- probabilistic simulation  
- AI interpretation  

and transforms them into a unified, institutional-style investment intelligence workflow.

The platform is designed to simulate how modern quantitative firms structure:

- market regime positioning  
- portfolio allocation  
- risk management  
- scenario analysis  
- capital deployment decisions  

into clear, decision-ready output.
---

## 🧩 Core Features
## 🔍 Stock Lens

Single-ticker analysis engine for live market structure, signal interpretation, and AI trader insight.

Features:
- Bullish / Neutral / Bearish signal classification
- Conviction score
- Risk level
- Real-time price and daily change
- Intraday market structure chart
- VWAP / EMA technical context
- Recent headline feed
- AI trader-style interpretation

👉 Stock Lens is the single-name intelligence layer of AInvest.


## 📊 Portfolio Lab

Multi-asset portfolio analysis system for portfolio construction, benchmark comparison, and PM-style review.

Features:
- Add multiple tickers dynamically
- Equal-weight or custom-weight portfolios
- Portfolio-level return analysis
- Volatility, Sharpe ratio, and max drawdown
- Benchmark comparison against SPY and strategy baskets
- Stress scenario simulation
- AI portfolio brief written in PM-style language

👉 Portfolio Lab is the portfolio intelligence layer of AInvest.


## ⚙️ Allocation Engine

Advanced capital allocation and portfolio construction workspace built for institutional-style analysis.

Dynamic portfolio construction based on:
- Mandate: growth, defensive, absolute return, opportunistic
- Risk budget
- Time horizon
- Portfolio size

Automatically generates:
- Capital deployment plan: ticker, shares, dollars, strategy sleeve
- Portfolio allocation map
- Projected return, volatility, drawdown, Sharpe ratio, and SPY outperformance
- Benchmark comparison against:
  - SPY
  - Growth Strategy
  - Concentrated Alpha
  - Defensive Allocation

Integrated analytical engines:
- Monte Carlo Engine
- Risk Engine
- Stress Test Engine
- Factor Exposure Engine
- Correlation Engine
- Scenario Engine
- Market Regime Engine
- AI Insights
- AI Recommendations Layer

Advanced analytics:
- Live price-based position sizing
- Risk contribution breakdown by allocation sleeve
- Recession, inflation, rates shock, tech selloff, credit crunch, and bull market stress testing
- Factor exposure analysis across market beta, size, value, momentum, quality, low volatility, and growth
- Correlation heatmap for overlap and diversification analysis
- Custom macro scenario builder for GDP, inflation, rates, and equity shocks
- Portfolio health scoring
- Strategic sleeve exposure visualization

AI layer:
- AI executive summary
- PM-style allocation brief
- Desk-style portfolio interpretation
- Exposure, positioning, adjustment, and risk commentary

👉 Allocation Engine transforms AInvest from a stock analysis dashboard into a multi-engine portfolio intelligence platform.

---
## System Architecture

AInvest operates as a layered financial intelligence pipeline designed to structure market data, quantitative analytics, simulation systems, and AI reasoning into a unified investment workflow.

### 1. Market Data Layer

Handles live market data ingestion, normalization, and preprocessing.

Responsibilities:
- Real-time financial data retrieval
- Historical return normalization
- Benchmark construction
- Cross-asset market monitoring
- Data cleaning and fallback handling
- Defensive runtime safeguards

Data sources:
- yfinance
- PostgreSQL ranked datasets
- Precomputed cloud allocation pipelines

---

### 2. Quantitative Signal Layer

Transforms raw market data into structured portfolio and market signals.

Capabilities:
- Directional bias generation
- Conviction scoring
- Risk classification
- Relative strength analysis
- Allocation ranking models
- Cross-asset signal evaluation
- Regime transition analysis

Outputs:
- Bullish / neutral / bearish classifications
- Portfolio bucket weights
- Macro regime classifications
- Stress indicators
- Factor exposure metrics

---

### 3. Portfolio Intelligence Layer

Performs portfolio construction, simulation, and risk analytics.

Systems include:
- Allocation Engine
- Portfolio Lab
- Risk Engine
- Stress Test Engine
- Correlation Engine
- Factor Exposure Engine
- Monte Carlo simulation framework

Capabilities:
- Capital deployment modeling
- Benchmark comparison
- Volatility analysis
- Drawdown forecasting
- Probabilistic scenario simulation
- Tail-risk evaluation
- Survivability testing

---

### 4. AI Reasoning Layer

LLMs interpret quantitative outputs into structured investment intelligence.

AI-generated outputs include:
- Trader-style signal interpretation
- PM-style portfolio briefs
- AI macro desk commentary
- Scenario interpretation
- Allocation rationale
- Risk observations

This layer converts quantitative outputs into decision-oriented financial intelligence.

---

### 5. Presentation Layer

Institutional-style decision interface built in Streamlit.

Design principles:
- Decision-first workflows
- Modular analytical engines
- High-density information layout
- Real-time market intelligence rendering
- Portfolio manager-style presentation

The interface is designed to resemble internal portfolio research and market intelligence systems rather than traditional retail dashboards.


---


## ☁️ Cloud Infrastructure & Data Pipeline (NEW)

AInvest now operates on a cloud-backed architecture designed for scalable financial computation workflows.

### Infrastructure Upgrades
- PostgreSQL database integration (Render)
- Autonomous cron-based ranking pipeline
- Persistent cloud storage for ranked candidates
- Background precomputation of allocation datasets
- Environment-based secret management
- Auto-deploy CI workflow through GitHub + Render

### Ranking Pipeline
The allocation engine no longer computes all market rankings on-demand.

Instead:
1. A scheduled cloud cron job scans and ranks securities
2. Rankings are stored in PostgreSQL
3. The UI retrieves precomputed datasets instantly
4. Allocation Engine consumes ranked candidates in real time

This architecture significantly improves:
- response speed
- scalability
- reliability
- separation of compute vs presentation layers

### Reliability Engineering
Recent upgrades introduced:
- ticker failure handling
- defensive runtime safeguards
- fallback-ready data architecture
- production bug tracking / hotfix workflow
- groundwork for future multi-provider market data routing

👉 These upgrades move AInvest closer to a real-world fintech systems architecture rather than a simple dashboard application.

---
## Institutional Market Intelligence Upgrade

AInvest now includes a live institutional-style market intelligence layer designed to mirror professional trading desk workflows.

New features added:

- Dynamic market session tracking
  - Pre-Market
  - Market Open
  - After Hours
  - Futures Session

- Real-time cross-asset monitoring:
  - S&P 500
  - Nasdaq
  - Dow Jones
  - VIX
  - Bitcoin
  - 10Y Treasury Yield

- Futures-aware after-hours architecture using:
  - ES futures
  - NQ futures
  - RTY futures

- AI-generated macro desk commentary
- Risk Pulse engine:
  - Risk-On
  - Risk-Off
  - Mixed regime detection

- Live market regime classification
- Institutional-style cross-asset intelligence strip
- Dynamic macro positioning interpretation
- Continuous session-aware market monitoring

👉 This upgrade transforms AInvest from a standard finance dashboard into a real-time institutional market intelligence platform inspired by hedge fund and trading desk infrastructure.

---

## 🔁 End-to-End Flow

1. User inputs ticker(s)  
2. Signal engine evaluates position  
3. Market data is retrieved  
4. AI generates context + reasoning  
5. Unified output is displayed  

---

## Capabilities

- Quantitative signal generation
- AI-driven market interpretation
- Real-time cross-asset monitoring
- Portfolio analytics and benchmarking
- Institutional-style portfolio construction
- Monte Carlo simulation and probabilistic modeling
- Stress testing and scenario analysis
- Market regime classification
- AI-generated macro desk commentary
- Risk-aware capital allocation workflows
- Factor exposure and correlation analysis
- Cloud-backed ranking and data pipelines
- Real-time portfolio intelligence systems
- Resilient market data handling and fallback architecture

---

## 🛠 Tech Stack

### Languages & Frameworks
- Python
- Streamlit

### Data & Analytics
- Pandas
- NumPy
- Plotly
- yfinance

### AI Layer
- OpenAI API
- GPT-4.1-mini

### Cloud Infrastructure
- Render
- PostgreSQL
- GitHub CI/CD
- Cron-based cloud pipelines

### Systems & Architecture
- Monte Carlo simulation engine
- Portfolio allocation engine
- Stress testing framework
- Correlation analysis engine
- Factor exposure system
- Market regime classification engine
- AI macro intelligence layer

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

AInvest is not built to predict markets with certainty.

It is built to:

> structure uncertainty into interpretable, probabilistic decision frameworks.

The platform focuses on:
- signal interpretation over prediction
- risk-aware portfolio construction
- macro regime identification
- probabilistic simulation
- scenario-driven analysis
- institutional-style decision support

Rather than generating isolated indicators, AInvest attempts to combine:

- quantitative analytics
- portfolio intelligence
- macro positioning
- simulation systems
- AI reasoning

into a unified investment workflow designed to resemble modern institutional research and portfolio systems.

---

## 🔮 Future Expansion

Planned expansion areas include:

- Advanced portfolio optimization systems
- Multi-timeframe signal aggregation
- Dynamic factor rotation models
- Beta / factor exposure decomposition
- Cross-asset macro correlation engines
- AI-assisted portfolio rebalancing
- Adaptive regime transition forecasting
- Probabilistic risk scoring systems
- Multi-provider market data routing
- Cloud-based precomputed ranking infrastructure
- Autonomous AI research agents
- Institutional watchlists + alert systems
- Scenario tree simulation frameworks
- Expanded Monte Carlo stress architectures
- Custom portfolio mandate creation
- AI-generated investment memos and research reports

Long-term vision:
- evolve AInvest from a financial dashboard into a full investment intelligence operating system.

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
