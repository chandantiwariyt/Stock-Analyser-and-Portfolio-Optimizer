import numpy as np
import pandas as pd


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute percentage returns from price data.
    """
    return prices.pct_change().dropna()


def annualized_returns(returns: pd.DataFrame, periods_per_year: int = 252) -> pd.Series:
    """
    Annualize mean periodic returns.
    """
    return returns.mean() * periods_per_year


def annualized_volatility(returns: pd.DataFrame, periods_per_year: int = 252) -> pd.Series:
    """
    Annualize periodic volatility.
    """
    return returns.std() * np.sqrt(periods_per_year)


def covariance_matrix(returns: pd.DataFrame, periods_per_year: int = 252) -> pd.DataFrame:
    """
    Annualized covariance matrix.
    """
    return returns.cov() * periods_per_year


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Correlation matrix for diversification analysis.
    """
    return returns.corr()


def drawdown_series(prices: pd.Series) -> pd.Series:
    running_max = prices.cummax()
    return prices / running_max - 1.0


def max_drawdown(prices: pd.Series) -> float:
    series = prices.dropna()
    if series.empty:
        return 0.0
    return float(drawdown_series(series).min())


def asset_drawdowns(prices: pd.DataFrame) -> pd.Series:
    return prices.apply(max_drawdown, axis=0)


def portfolio_price_series(prices: pd.DataFrame, weights: pd.Series) -> pd.Series:
    normalized = prices.dropna().copy()
    rebased = normalized / normalized.iloc[0]
    return rebased.mul(weights, axis=1).sum(axis=1)
