# Stock Portfolio Optimizer

An interactive Streamlit app for portfolio analysis across Indian and U.S. stocks with INR-aware pricing, exact optimization, benchmark comparison, watchlist tracking, and plain-English portfolio commentary.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![Plotly](https://img.shields.io/badge/Plotly-5.x-purple)
![SciPy](https://img.shields.io/badge/SciPy-Optimization-orange)

## What This App Does

- Optimizes stock portfolios using both Monte Carlo simulation and exact `scipy` optimization
- Supports Indian and U.S. stocks in the same workflow
- Shows Indian stocks in INR at native market price
- Converts non-INR stocks like `AAPL` into INR for comparison
- Tracks selected tickers in a separate watchlist tab
- Compares portfolio performance against `NIFTY 50` and `S&P 500`
- Calculates per-stock and portfolio drawdown
- Suggests rupee allocation amounts based on your portfolio size
- Generates a downloadable PDF summary
- Produces simple `Buy`, `Hold`, or `Sell` suggestions from market conditions
- Adds plain-English AI-style commentary from the computed metrics

## 🔴 Live Demo
> Run locally using the steps below — or Live deployment on [Streamlit Cloud](https://stock-analyser-and-portfolio-optimizer.onrender.com/)

## Current Features

### Optimizer

- Custom date range: `1M`, `3M`, `6M`, `1Y`, `3Y`, `5Y`
- Monte Carlo efficient frontier
- Exact max-Sharpe portfolio
- Exact minimum-volatility portfolio
- Correlation heatmap
- Asset breakdown with volatility, Sharpe, drawdown, and decision signal
- Benchmark comparison chart and stats
- Rupee allocation table
- PDF export
- AI-style summary commentary

### Watchlist

- Add Indian or U.S. stocks
- Track live price, previous close, daily change, and INR value
- Keep Indian stocks in rupees without incorrect USD multiplication
- Convert foreign stocks into INR for display

## Why INR Handling Matters

This project treats Indian and U.S. stocks differently on purpose:

- Indian stocks like `BHEL` stay in INR because their market price is already in rupees
- U.S. stocks like `AAPL` are converted into INR so you can compare them in one currency view

This avoids the common mistake of multiplying an Indian stock price by the USD-INR rate and showing a fake price.

## Tech Stack

- `streamlit` for the web app UI
- `plotly` for interactive charts
- `pandas` and `numpy` for data processing
- `yfinance` for price data
- `scipy` for exact optimization

## Project Structure

```text
repo/
├── app.py
├── requirements.txt
├── readme.md
├── data/
│   └── fetcher.py
├── mpt/
│   ├── montecarlo.py
│   └── returns.py
└── charts/
    └── plotter.py
```

## Run Locally

```bash
git clone https://github.com/chandantiwariyt/Portfolio-Optimizer-watchlist.git
cd Portfolio-Optimizer-watchlist
pip install -r requirements.txt
streamlit run app.py
```

If `streamlit` is not recognized on your machine:

```bash
python -m streamlit run app.py
```

Then open the local URL shown in the terminal, usually:

`http://localhost:8501`

## How To Use

1. Enter stock tickers in the sidebar
2. Choose a date range
3. Set your risk-free rate
4. Enter your portfolio size in INR
5. Click `Run Analysis`
6. Review:
   - optimized portfolio metrics
   - benchmark comparison
   - drawdown analysis
   - allocation table
   - market-condition suggestions
   - watchlist prices

## Example Tickers

- U.S. stocks: `AAPL`, `MSFT`, `NVDA`, `GOOGL`, `AMZN`
- Indian stocks: `BHEL`, `RELIANCE`, `TCS`, `INFY`, `SBIN`

You can also use exchange-specific symbols if needed, such as:

- `BHEL.NS`
- `RELIANCE.NS`
- `TCS.NS`

## Notes

- Price data depends on Yahoo Finance availability
- Benchmark calendars differ between India and U.S. markets, so the app aligns them safely before comparison
- Generated `__pycache__` files are not part of the source code changes

## Author

Built by **Chandan Tiwari**

- GitHub: [chandantiwariyt](https://github.com/chandantiwariyt)
- LinkedIn: [chandantiwari4](https://www.linkedin.com/in/chandantiwari4/)
