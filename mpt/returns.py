# mpt/returns.py

import numpy as np
import pandas as pd


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute monthly percentage returns from price data.
    """
    returns = prices.pct_change().dropna()
    print(f"✅ Computed returns — {len(returns)} monthly observations per stock")
    return returns


def annualized_returns(returns: pd.DataFrame) -> pd.Series:
    """
    Annualize mean monthly returns (multiply by 12).
    """
    ann_ret = returns.mean() * 12
    print("\n--- Annualized Expected Returns ---")
    for ticker, val in ann_ret.items():
        print(f"  {ticker:8s}  {val*100:+.2f}%")
    return ann_ret


def annualized_volatility(returns: pd.DataFrame) -> pd.Series:
    """
    Annualize volatility — std dev of monthly returns × sqrt(12).
    """
    ann_vol = returns.std() * np.sqrt(12)
    print("\n--- Annualized Volatility (Risk) ---")
    for ticker, val in ann_vol.items():
        print(f"  {ticker:8s}  {val*100:.2f}%")
    return ann_vol


def covariance_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Annualized covariance matrix (monthly cov × 12).
    """
    cov = returns.cov() * 12
    print("\n--- Covariance Matrix ---")
    print(cov.round(6))
    return cov


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Correlation matrix — useful for spotting diversification.
    """
    corr = returns.corr()
    print("\n--- Correlation Matrix ---")
    print(corr.round(3))
    return corr


if __name__ == "__main__":
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from data.fetcher import fetch_prices

    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    prices  = fetch_prices(tickers)

    returns = compute_returns(prices)
    ann_ret = annualized_returns(returns)
    ann_vol = annualized_volatility(returns)
    cov     = covariance_matrix(returns)
    corr    = correlation_matrix(returns)