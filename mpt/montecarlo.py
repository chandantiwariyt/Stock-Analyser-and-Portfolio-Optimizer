# mpt/montecarlo.py

import numpy as np
import pandas as pd


def run_monte_carlo(
    ann_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float = 0.043,
    n_simulations: int = 10_000
) -> pd.DataFrame:
    """
    Randomly generate 10,000 portfolios and compute their
    return, volatility, and Sharpe ratio.
    Returns a DataFrame of all simulated portfolios.
    """
    tickers = ann_returns.index.tolist()
    n_assets = len(tickers)
    results  = []

    print(f"⚙️  Running {n_simulations:,} Monte Carlo simulations...")

    for _ in range(n_simulations):
        # Random weights that sum to 1
        w = np.random.random(n_assets)
        w /= w.sum()

        # Portfolio return & volatility
        port_return = np.dot(w, ann_returns.values)
        port_vol    = np.sqrt(w @ cov_matrix.values @ w)
        sharpe      = (port_return - risk_free_rate) / port_vol

        results.append({
            "return":     port_return,
            "volatility": port_vol,
            "sharpe":     sharpe,
            **dict(zip(tickers, w))   # store each weight
        })

    df = pd.DataFrame(results)
    print(f"✅ Done — {len(df):,} portfolios simulated\n")
    return df


def get_optimal_portfolios(mc_df: pd.DataFrame) -> dict:
    """
    Extract Max Sharpe and Min Volatility portfolios.
    """
    max_sharpe = mc_df.loc[mc_df["sharpe"].idxmax()]
    min_vol    = mc_df.loc[mc_df["volatility"].idxmin()]

    print("--- Max Sharpe Portfolio ---")
    print(f"  Return:     {max_sharpe['return']*100:.2f}%")
    print(f"  Volatility: {max_sharpe['volatility']*100:.2f}%")
    print(f"  Sharpe:     {max_sharpe['sharpe']:.4f}")

    print("\n--- Min Volatility Portfolio ---")
    print(f"  Return:     {min_vol['return']*100:.2f}%")
    print(f"  Volatility: {min_vol['volatility']*100:.2f}%")
    print(f"  Sharpe:     {min_vol['sharpe']:.4f}")

    return {"max_sharpe": max_sharpe, "min_vol": min_vol}


def get_weights(portfolio: pd.Series, tickers: list[str]) -> pd.Series:
    """
    Extract and display clean weights from a portfolio row.
    """
    weights = portfolio[tickers]
    print("\n--- Optimal Weights ---")
    for ticker, w in weights.items():
        bar = "█" * int(w * 40)
        print(f"  {ticker:8s} {w*100:5.1f}%  {bar}")
    return weights


if __name__ == "__main__":
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from data.fetcher import fetch_prices
    from mpt.returns  import compute_returns, annualized_returns, covariance_matrix

    tickers  = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    prices   = fetch_prices(tickers)
    returns  = compute_returns(prices)
    ann_ret  = annualized_returns(returns)
    cov      = covariance_matrix(returns)

    mc_df    = run_monte_carlo(ann_ret, cov)
    optimal  = get_optimal_portfolios(mc_df)
    weights  = get_weights(optimal["max_sharpe"], tickers)