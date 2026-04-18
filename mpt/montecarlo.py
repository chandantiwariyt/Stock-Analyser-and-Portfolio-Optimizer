import numpy as np
import pandas as pd
from scipy.optimize import minimize


def portfolio_return(weights: np.ndarray, ann_returns: pd.Series) -> float:
    return float(np.dot(weights, ann_returns.values))


def portfolio_volatility(weights: np.ndarray, cov_matrix: pd.DataFrame) -> float:
    return float(np.sqrt(weights @ cov_matrix.values @ weights))


def portfolio_sharpe(
    weights: np.ndarray,
    ann_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float,
) -> float:
    volatility = portfolio_volatility(weights, cov_matrix)
    if volatility == 0:
        return 0.0
    return (portfolio_return(weights, ann_returns) - risk_free_rate) / volatility


def run_monte_carlo(
    ann_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float = 0.043,
    n_simulations: int = 10_000,
) -> pd.DataFrame:
    tickers = ann_returns.index.tolist()
    n_assets = len(tickers)
    results = []

    for _ in range(n_simulations):
        weights = np.random.random(n_assets)
        weights /= weights.sum()

        results.append(
            {
                "return": portfolio_return(weights, ann_returns),
                "volatility": portfolio_volatility(weights, cov_matrix),
                "sharpe": portfolio_sharpe(weights, ann_returns, cov_matrix, risk_free_rate),
                **dict(zip(tickers, weights)),
            }
        )

    return pd.DataFrame(results)


def _solve_weights(ann_returns: pd.Series, cov_matrix: pd.DataFrame, objective) -> np.ndarray:
    n_assets = len(ann_returns)
    initial = np.ones(n_assets) / n_assets
    bounds = [(0.0, 1.0)] * n_assets
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    result = minimize(
        objective,
        x0=initial,
        bounds=bounds,
        constraints=constraints,
        method="SLSQP",
    )
    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")
    return result.x


def optimize_max_sharpe(
    ann_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float = 0.043,
) -> pd.Series:
    weights = _solve_weights(
        ann_returns,
        cov_matrix,
        lambda w: -portfolio_sharpe(w, ann_returns, cov_matrix, risk_free_rate),
    )
    return pd.Series(
        {
            "return": portfolio_return(weights, ann_returns),
            "volatility": portfolio_volatility(weights, cov_matrix),
            "sharpe": portfolio_sharpe(weights, ann_returns, cov_matrix, risk_free_rate),
            **dict(zip(ann_returns.index.tolist(), weights)),
        }
    )


def optimize_min_volatility(
    ann_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float = 0.043,
) -> pd.Series:
    weights = _solve_weights(
        ann_returns,
        cov_matrix,
        lambda w: portfolio_volatility(w, cov_matrix),
    )
    return pd.Series(
        {
            "return": portfolio_return(weights, ann_returns),
            "volatility": portfolio_volatility(weights, cov_matrix),
            "sharpe": portfolio_sharpe(weights, ann_returns, cov_matrix, risk_free_rate),
            **dict(zip(ann_returns.index.tolist(), weights)),
        }
    )


def get_optimal_portfolios(mc_df: pd.DataFrame) -> dict:
    return {
        "max_sharpe": mc_df.loc[mc_df["sharpe"].idxmax()],
        "min_vol": mc_df.loc[mc_df["volatility"].idxmin()],
    }
