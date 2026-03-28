# data/fetcher.py

import yfinance as yf
import pandas as pd

def fetch_prices(tickers: list[str], period: str = "1y", interval: str = "1mo") -> pd.DataFrame:
    """
    Fetch monthly closing prices for a list of tickers.
    Returns a DataFrame where each column is a ticker, rows are dates.
    """
    raw = yf.download(tickers, period=period, interval=interval, auto_adjust=True)

    # Extract just the closing prices
    if len(tickers) == 1:
        prices = raw[["Close"]].rename(columns={"Close": tickers[0]})
    else:
        prices = raw["Close"]

    # Drop any rows where ALL prices are missing
    prices.dropna(how="all", inplace=True)

    print(f"✅ Fetched {len(prices)} months of data for: {', '.join(tickers)}")
    return prices


if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    df = fetch_prices(tickers)
    print("\n--- Price Table ---")
    print(df.round(2))
    print(f"\nShape: {df.shape}  →  {df.shape[0]} months × {df.shape[1]} stocks")