
# AInvest
### AI-Powered Stock Insight Engine

> AInvest transforms stock data into **clear, AI-generated insights** by combining model-driven signals, live market data, and natural language explanations.

---

## 🚀 Live App  
https://ainvest-8zkq.onrender.com  

---

## 📸 Screenshots  

 ### Top Model Pick
![Top Pick](assets/ainvest:assets:top_pick.png)



### Stock Analysis + AI Insight
![Analysis](assets/ainvest:assets:analysis.png)


---

## 🧠 Overview  

AInvest is an AI-powered stock analysis tool that:

- Ranks stocks using a machine learning signal model  
- Falls back to real-time market data when needed  
- Generates **AI explanations** to interpret stock behavior  
- Presents insights through a clean, interactive UI  

Instead of just showing numbers, AInvest answers:

**“What is actually happening with this stock?”**

---

## 🔥 Key Features  

- 📊 Model-Based Rankings  
  Precomputed signals rank top stocks by predicted return probability  

- 🔁 Live Data Fallback (yfinance)  
  Any ticker can be analyzed in real time  

- 🤖 AI Market Insight Engine  
  OpenAI generates contextual explanations of price movement  

- ⚡ Fast UI with Precomputed Data  
  Signals are loaded instantly from disk  

- 📈 Interactive Price Charts  
  Visualize recent price movement dynamically  

---

## 🏗️ Architecture  

User Input  
↓  
Check Model Signals (CSV)  
↓  
If Found → Use Model Output  
Else → Fetch Live Data (yfinance)  
↓  
Compute Metrics (price, change, confidence)  
↓  
Generate AI Explanation (OpenAI)  
↓  
Render UI (Streamlit)  

---

## ⚙️ Tech Stack  

- Python  
- Pandas  
- Streamlit  
- yfinance  
- OpenAI API  

---

## ⚡ Performance Design  

To ensure fast load times:

- Signals are precomputed offline  
- App reads results instantly from disk  
- Avoids expensive real-time model computation  
- Uses lightweight fallback for live queries  

---

## 💡 Key Insight  

Separating model computation from the UI allows the app to remain fast while still delivering meaningful, AI-powered insights.

---

## 🧪 Running Locally  

git clone https://github.com/dane-anderson/ainvest.git  
cd ainvest  

pip install -r requirements.txt  

export OPENAI_API_KEY="your_key_here"  

streamlit run app.py  

---

## ⚠️ Disclaimer  

This project is for educational purposes only and does not constitute financial advice.
