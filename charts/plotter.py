# charts/plotter.py

import plotly.graph_objects as go
import pandas as pd


def plot_efficient_frontier(
    mc_df: pd.DataFrame,
    max_sharpe: pd.Series,
    min_vol: pd.Series,
    tickers: list[str]
):
    """
    Plot the efficient frontier with all simulated portfolios,
    color-graded by Sharpe ratio. Highlights Max Sharpe & Min Vol.
    """

    fig = go.Figure()

    # ── All simulated portfolios (scatter, colored by Sharpe) ──
    fig.add_trace(go.Scatter(
        x=mc_df["volatility"] * 100,
        y=mc_df["return"] * 100,
        mode="markers",
        marker=dict(
            size=4,
            color=mc_df["sharpe"],
            colorscale=[
                [0.0,  "#4B7CF3"],
                [0.5,  "#00D9A3"],
                [1.0,  "#F0B429"]
            ],
            colorbar=dict(title="Sharpe Ratio", thickness=14),
            opacity=0.6
        ),
        name="Simulated Portfolios",
        hovertemplate="Return: %{y:.1f}%<br>Volatility: %{x:.1f}%<extra></extra>"
    ))

    # ── Max Sharpe Portfolio ──
    fig.add_trace(go.Scatter(
        x=[max_sharpe["volatility"] * 100],
        y=[max_sharpe["return"] * 100],
        mode="markers+text",
        marker=dict(size=16, color="#F0B429", symbol="star"),
        text=["Max Sharpe"],
        textposition="top center",
        textfont=dict(color="#F0B429", size=12),
        name=f"Max Sharpe  ({max_sharpe['sharpe']:.2f})",
        hovertemplate=f"Return: {max_sharpe['return']*100:.1f}%<br>Vol: {max_sharpe['volatility']*100:.1f}%<br>Sharpe: {max_sharpe['sharpe']:.4f}<extra></extra>"
    ))

    # ── Min Volatility Portfolio ──
    fig.add_trace(go.Scatter(
        x=[min_vol["volatility"] * 100],
        y=[min_vol["return"] * 100],
        mode="markers+text",
        marker=dict(size=14, color="#00D9A3", symbol="triangle-up"),
        text=["Min Vol"],
        textposition="top center",
        textfont=dict(color="#00D9A3", size=12),
        name=f"Min Volatility  ({min_vol['volatility']*100:.1f}%)",
        hovertemplate=f"Return: {min_vol['return']*100:.1f}%<br>Vol: {min_vol['volatility']*100:.1f}%<br>Sharpe: {min_vol['sharpe']:.4f}<extra></extra>"
    ))

    # ── Layout ──
    fig.update_layout(
        title=dict(
            text="Efficient Frontier — Modern Portfolio Theory",
            font=dict(size=20, color="#E2E6F0")
        ),
        xaxis=dict(
            title="Annualized Volatility (%)",
            gridcolor="#1C2238",
            color="#A8B3CC"
        ),
        yaxis=dict(
            title="Annualized Expected Return (%)",
            gridcolor="#1C2238",
            color="#A8B3CC"
        ),
        paper_bgcolor="#060810",
        plot_bgcolor="#0C0F1A",
        legend=dict(
            bgcolor="#111521",
            bordercolor="#1C2238",
            borderwidth=1,
            font=dict(color="#A8B3CC")
        ),
        font=dict(family="monospace"),
        width=900, height=580
    )

    fig.show()
    print("✅ Chart opened in browser")


def plot_allocation_pie(max_sharpe: pd.Series, tickers: list[str]):
    """
    Donut chart of optimal weights for the Max Sharpe portfolio.
    """
    weights = [max_sharpe[t] for t in tickers]
    colors  = ["#F0B429","#00D9A3","#4B7CF3","#FF4560","#9B59B6",
               "#00B4D8","#F72585","#06D6A0","#FFB703","#3A86FF"]

    fig = go.Figure(go.Pie(
        labels=tickers,
        values=[round(w * 100, 2) for w in weights],
        hole=0.55,
        marker=dict(colors=colors[:len(tickers)], line=dict(color="#060810", width=3)),
        textinfo="label+percent",
        textfont=dict(size=13, color="#E2E6F0"),
        hovertemplate="%{label}: %{value:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title=dict(
            text="Optimal Portfolio Allocation (Max Sharpe)",
            font=dict(size=18, color="#E2E6F0")
        ),
        paper_bgcolor="#060810",
        font=dict(family="monospace", color="#A8B3CC"),
        legend=dict(bgcolor="#111521", bordercolor="#1C2238", borderwidth=1),
        width=600, height=500
    )

    fig.show()
    print("✅ Allocation chart opened in browser")


if __name__ == "__main__":
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from data.fetcher     import fetch_prices
    from mpt.returns      import compute_returns, annualized_returns, covariance_matrix
    from mpt.montecarlo   import run_monte_carlo, get_optimal_portfolios

    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    prices  = fetch_prices(tickers)
    returns = compute_returns(prices)
    ann_ret = annualized_returns(returns)
    cov     = covariance_matrix(returns)

    mc_df   = run_monte_carlo(ann_ret, cov)
    optimal = get_optimal_portfolios(mc_df)

    plot_efficient_frontier(mc_df, optimal["max_sharpe"], optimal["min_vol"], tickers)
    plot_allocation_pie(optimal["max_sharpe"], tickers)