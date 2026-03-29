# 📈 Stock Portfolio Optimizer — Modern Portfolio Theory

An interactive portfolio optimization tool built with Python that uses
**Modern Portfolio Theory (MPT)** and **Monte Carlo simulation** to find
the mathematically optimal asset allocation across any set of stocks.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![Plotly](https://img.shields.io/badge/Plotly-5.x-purple)

---

## 🚀 Live Demo
> Run locally using the steps below — or deploy free on [Streamlit Cloud] (https://portfolio-optimizer-fp0l.onrender.com/)

---

## 📌 What It Does

- **Fetches real market data** — 12 months of historical prices via `yfinance`
- **Computes MPT statistics** — annualized returns, volatility (σ), covariance matrix
- **Runs 10,000 Monte Carlo simulations** — randomly weighted portfolios mapping the full risk/return universe
- **Finds the optimal portfolio** — maximizes the Sharpe ratio (risk-adjusted return)
- **Visualizes the efficient frontier** — interactive scatter plot color-graded by Sharpe ratio
- **Asset breakdown table** — per-stock return, volatility, Sharpe, and correlation

---

## 🧠 Key Concepts

| Concept | Description |
|---|---|
| **Efficient Frontier** | The set of portfolios with the highest return for a given level of risk |
| **Sharpe Ratio** | `(Return - RiskFreeRate) / Volatility` — measures risk-adjusted performance |
| **Max Sharpe Portfolio** | The single optimal portfolio on the efficient frontier |
| **Min Volatility Portfolio** | The lowest-risk portfolio regardless of return |
| **Covariance Matrix** | Captures how stocks move together — key to diversification |

---

## 🛠️ Tech Stack

- `yfinance` — market data fetching
- `numpy` / `pandas` — numerical computing & data wrangling
- `plotly` — interactive charts
- `streamlit` — web app UI
- `scipy` — scientific computing

---

## ⚙️ Setup
```bash
git clone https://github.com/YOUR_USERNAME/portfolio-optimizer.git
cd portfolio-optimizer
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Project Structure
```
portfolio-optimizer/
├── data/
│   └── fetcher.py        # yfinance price fetching
├── mpt/
│   ├── returns.py        # annualized returns, volatility, covariance
│   └── montecarlo.py     # 10,000 simulation engine
├── charts/
│   └── plotter.py        # Plotly efficient frontier & allocation charts
├── app.py                # Streamlit web app
└── requirements.txt
```

---

## 📊 Example Output

**Max Sharpe Portfolio** (AAPL, MSFT, GOOGL, AMZN, NVDA):
- Expected Return: ~34%
- Volatility: ~28%
- Sharpe Ratio: ~1.07

---

## 👤 Author
Built by **Chandan Tiwari** — [LinkedIn](https://www.linkedin.com/in/chandantiwari4/) · [GitHub](https://github.com/chandantiwariyt)
