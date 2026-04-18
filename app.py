import os
import sys
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.dirname(__file__))

from data.fetcher import fetch_prices, fetch_watchlist_prices
from mpt.montecarlo import (
    get_optimal_portfolios,
    optimize_max_sharpe,
    optimize_min_volatility,
    run_monte_carlo,
)
from mpt.returns import (
    annualized_returns,
    annualized_volatility,
    asset_drawdowns,
    compute_returns,
    correlation_matrix,
    covariance_matrix,
    max_drawdown,
    portfolio_price_series,
)


DATE_RANGE_OPTIONS = {
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "3Y": "3y",
    "5Y": "5y",
}

BENCHMARKS = {
    "NIFTY 50": "^NSEI",
    "S&P 500": "^GSPC",
}


def format_inr(value: float) -> str:
    return f"₹{value:,.2f}"


def build_simple_pdf(lines: list[str]) -> bytes:
    escaped_lines = []
    for line in lines:
        safe = (
            line.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .encode("ascii", "replace")
            .decode("ascii")
        )
        escaped_lines.append(safe)

    content_parts = ["BT", "/F1 11 Tf", "50 780 Td", "14 TL"]
    for index, line in enumerate(escaped_lines):
        if index == 0:
            content_parts.append(f"({line}) Tj")
        else:
            content_parts.append("T*")
            content_parts.append(f"({line}) Tj")
    content_parts.append("ET")
    content_stream = "\n".join(content_parts).encode("ascii")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(
        f"5 0 obj << /Length {len(content_stream)} >> stream\n".encode("ascii")
        + content_stream
        + b"\nendstream endobj\n"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer << /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode("ascii")
    )
    return bytes(pdf)


def generate_commentary(
    exact_max_sharpe: pd.Series,
    exact_min_vol: pd.Series,
    portfolio_drawdown: float,
    benchmark_stats: pd.DataFrame,
    weights: pd.Series,
) -> str:
    top_weight = weights.sort_values(ascending=False).index[0]
    return (
        f"The exact optimizer currently places the highest weight on {top_weight}. "
        f"The max-Sharpe portfolio targets an annualized return of {exact_max_sharpe['return'] * 100:.2f}% "
        f"with volatility near {exact_max_sharpe['volatility'] * 100:.2f}% and a Sharpe ratio of "
        f"{exact_max_sharpe['sharpe']:.2f}. The worst peak-to-trough decline for the optimized portfolio "
        f"over the selected window was {portfolio_drawdown * 100:.2f}%. Over the same period, the portfolio "
        f"returned {benchmark_stats.loc['Portfolio', 'Cumulative Return (%)']:.2f}% versus "
        f"{benchmark_stats.loc['NIFTY 50', 'Cumulative Return (%)']:.2f}% for NIFTY 50 and "
        f"{benchmark_stats.loc['S&P 500', 'Cumulative Return (%)']:.2f}% for the S&P 500. "
        f"If you want a steadier profile, the minimum-volatility portfolio reduces expected return to "
        f"{exact_min_vol['return'] * 100:.2f}% in exchange for lower risk."
    )


def build_report_lines(
    tickers: list[str],
    period_label: str,
    exact_max_sharpe: pd.Series,
    allocation_df: pd.DataFrame,
    benchmark_stats: pd.DataFrame,
    commentary: str,
) -> list[str]:
    lines = [
        "Portfolio Optimizer Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Date Range: {period_label}",
        f"Tickers: {', '.join(tickers)}",
        "",
        "Exact Max-Sharpe Portfolio",
        f"Expected Return: {exact_max_sharpe['return'] * 100:.2f}%",
        f"Volatility: {exact_max_sharpe['volatility'] * 100:.2f}%",
        f"Sharpe Ratio: {exact_max_sharpe['sharpe']:.2f}",
        "",
        "Rupee Allocation",
    ]

    for row in allocation_df.itertuples(index=False):
        lines.append(
            f"{row.Ticker}: weight {row[1]:.2f}%, amount {row[2]:,.2f} INR, units {row[3]:.4f}"
        )

    lines.extend(["", "Benchmark Comparison"])
    for row in benchmark_stats.itertuples():
        lines.append(
            f"{row.Index}: cumulative return {row[1]:.2f}%, annualized return {row[2]:.2f}%, max drawdown {row[3]:.2f}%"
        )

    lines.extend(["", "AI Commentary", commentary])
    return lines


@st.cache_data(ttl=3600, show_spinner=False)
def load_prices(tickers: tuple[str, ...], period: str = "1y", interval: str = "1mo") -> pd.DataFrame:
    return fetch_prices(list(tickers), period=period, interval=interval)


@st.cache_data(ttl=900, show_spinner=False)
def load_watchlist(entries: tuple[tuple[str, str], ...]) -> pd.DataFrame:
    payload = [{"symbol": symbol, "market": market} for symbol, market in entries]
    return fetch_watchlist_prices(payload)


if "watchlist" not in st.session_state:
    st.session_state.watchlist = [
        {"symbol": "BHEL", "market": "India (NSE)"},
        {"symbol": "AAPL", "market": "United States"},
    ]


st.set_page_config(
    page_title="Portfolio Optimizer",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
<style>
  body, .stApp { background-color: #060810; color: #E2E6F0; }
  .metric-card {
    background: #111521; border: 1px solid #1C2238;
    border-radius: 10px; padding: 18px; text-align: center;
  }
  .metric-label { font-size: 11px; color: #5A6882; letter-spacing: 2px; text-transform: uppercase; }
  .metric-value { font-size: 28px; font-weight: 700; margin-top: 6px; }
  .gold  { color: #F0B429; }
  .green { color: #00D9A3; }
  .blue  { color: #4B7CF3; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("## 📈 Stock Portfolio Optimizer")
st.markdown("*Portfolio analytics with INR-first pricing and mixed-market support*")
st.caption(
    "Indian stocks stay in rupees at their native market price. "
    "Non-INR stocks, such as AAPL, are converted to INR only for display."
)
st.divider()

with st.sidebar:
    st.markdown("### ⚙️ Optimizer Settings")

    raw_input = st.text_input(
        "Tickers (comma-separated)",
        value="AAPL, MSFT, GOOGL, AMZN, NVDA",
        help="You can enter Indian stocks as `BHEL` or `BHEL.NS`, and U.S. stocks as `AAPL`.",
    )
    tickers = [t.strip().upper() for t in raw_input.split(",") if t.strip()]
    period_label = st.selectbox("Custom Date Range", options=list(DATE_RANGE_OPTIONS.keys()), index=3)
    period = DATE_RANGE_OPTIONS[period_label]

    risk_free = st.slider(
        "Risk-Free Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=4.3,
        step=0.1,
    ) / 100

    n_sims = st.selectbox(
        "Monte Carlo Simulations",
        options=[1_000, 5_000, 10_000, 20_000],
        index=2,
    )

    investment_amount = st.number_input(
        "Portfolio Size (INR)",
        min_value=1000.0,
        value=100000.0,
        step=1000.0,
    )

    run = st.button("🚀 Run Analysis", use_container_width=True)

    st.divider()
    st.markdown("### 👀 Watchlist Tips")
    st.markdown(
        """
        - Use the **Watchlist** tab to track current prices
        - Pick the market when adding Indian shares like `BHEL`
        - U.S. prices are shown in INR after conversion
        - Indian prices stay in INR without any USD conversion
        """
    )

optimizer_tab, watchlist_tab = st.tabs(["Optimizer", "Watchlist"])

with optimizer_tab:
    st.markdown("### Portfolio Optimizer")
    st.caption("Monte Carlo is used for the frontier view, while scipy is used for exact max-Sharpe and minimum-volatility portfolios.")

    if not run:
        st.info("Add your tickers in the sidebar and click **Run Analysis**.")
    elif len(tickers) < 2:
        st.error("Please enter at least 2 tickers.")
    else:
        try:
            with st.spinner("Fetching price data..."):
                prices = load_prices(tuple(tickers), period=period, interval="1d")
                benchmark_prices = load_prices(tuple(BENCHMARKS.values()), period=period, interval="1d")
                current_prices = load_watchlist(tuple((ticker, "") for ticker in tickers)).set_index("Ticker")

            with st.spinner("Computing returns, drawdown, and covariance..."):
                returns = compute_returns(prices)
                ann_ret = annualized_returns(returns)
                ann_vol = annualized_volatility(returns)
                cov = covariance_matrix(returns)
                corr = correlation_matrix(returns)
                dd_assets = asset_drawdowns(prices)

            with st.spinner(f"Running {n_sims:,} Monte Carlo simulations and exact optimization..."):
                mc_df = run_monte_carlo(ann_ret, cov, risk_free_rate=risk_free, n_simulations=n_sims)
                random_optimal = get_optimal_portfolios(mc_df)
                exact_max_sharpe = optimize_max_sharpe(ann_ret, cov, risk_free_rate=risk_free)
                exact_min_vol = optimize_min_volatility(ann_ret, cov, risk_free_rate=risk_free)

            weights = exact_max_sharpe[tickers]
            portfolio_series = portfolio_price_series(prices[tickers], weights)
            portfolio_drawdown = max_drawdown(portfolio_series)

            benchmark_rebased = benchmark_prices / benchmark_prices.iloc[0]
            benchmark_df = pd.DataFrame(
                {
                    "Portfolio": portfolio_series / portfolio_series.iloc[0],
                    "NIFTY 50": benchmark_rebased["^NSEI"],
                    "S&P 500": benchmark_rebased["^GSPC"],
                }
            ).dropna()

            benchmark_stats = pd.DataFrame(
                {
                    "Cumulative Return (%)": ((benchmark_df.iloc[-1] / benchmark_df.iloc[0]) - 1.0) * 100,
                    "Annualized Return (%)": benchmark_df.pct_change().dropna().mean() * 252 * 100,
                    "Max Drawdown (%)": benchmark_df.apply(max_drawdown) * 100,
                }
            )

            allocation_rows = []
            for ticker in tickers:
                live_price_inr = float(current_prices.loc[ticker, "Price (INR)"])
                allocated = investment_amount * float(weights[ticker])
                units = allocated / live_price_inr if live_price_inr else 0.0
                allocation_rows.append(
                    {
                        "Ticker": ticker,
                        "Weight (%)": round(float(weights[ticker]) * 100, 2),
                        "Amount (INR)": round(allocated, 2),
                        "Estimated Units": round(units, 4),
                    }
                )
            allocation_df = pd.DataFrame(allocation_rows)

            commentary = generate_commentary(
                exact_max_sharpe,
                exact_min_vol,
                portfolio_drawdown,
                benchmark_stats,
                weights,
            )
            report_lines = build_report_lines(
                tickers,
                period_label,
                exact_max_sharpe,
                allocation_df,
                benchmark_stats,
                commentary,
            )
            pdf_bytes = build_simple_pdf(report_lines)

            st.success("Analysis complete.")
            st.divider()

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Exact Max Sharpe</div>
                        <div class="metric-value gold">{exact_max_sharpe['sharpe']:.2f}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            with c2:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Expected Return</div>
                        <div class="metric-value green">{exact_max_sharpe['return'] * 100:.1f}%</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            with c3:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Portfolio Volatility</div>
                        <div class="metric-value blue">{exact_max_sharpe['volatility'] * 100:.1f}%</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            with c4:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Portfolio Drawdown</div>
                        <div class="metric-value">{portfolio_drawdown * 100:.1f}%</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.divider()

            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown("#### Efficient Frontier")
                fig_ef = go.Figure()
                fig_ef.add_trace(
                    go.Scatter(
                        x=mc_df["volatility"] * 100,
                        y=mc_df["return"] * 100,
                        mode="markers",
                        marker=dict(
                            size=3,
                            color=mc_df["sharpe"],
                            colorscale=[[0, "#4B7CF3"], [0.5, "#00D9A3"], [1, "#F0B429"]],
                            colorbar=dict(title="Sharpe"),
                            opacity=0.5,
                        ),
                        name="Monte Carlo",
                    )
                )
                fig_ef.add_trace(
                    go.Scatter(
                        x=[exact_max_sharpe["volatility"] * 100],
                        y=[exact_max_sharpe["return"] * 100],
                        mode="markers+text",
                        marker=dict(size=15, color="#F0B429", symbol="star"),
                        text=["Exact Max Sharpe"],
                        textposition="top center",
                        textfont=dict(color="#F0B429"),
                        name="Exact Max Sharpe",
                    )
                )
                fig_ef.add_trace(
                    go.Scatter(
                        x=[exact_min_vol["volatility"] * 100],
                        y=[exact_min_vol["return"] * 100],
                        mode="markers+text",
                        marker=dict(size=13, color="#00D9A3", symbol="triangle-up"),
                        text=["Exact Min Vol"],
                        textposition="top center",
                        textfont=dict(color="#00D9A3"),
                        name="Exact Min Vol",
                    )
                )
                fig_ef.add_trace(
                    go.Scatter(
                        x=[random_optimal["max_sharpe"]["volatility"] * 100],
                        y=[random_optimal["max_sharpe"]["return"] * 100],
                        mode="markers",
                        marker=dict(size=10, color="#9B59B6"),
                        name="Best Monte Carlo",
                    )
                )
                fig_ef.update_layout(
                    paper_bgcolor="#0C0F1A",
                    plot_bgcolor="#0C0F1A",
                    font=dict(color="#A8B3CC"),
                    xaxis=dict(title="Volatility (%)", gridcolor="#1C2238"),
                    yaxis=dict(title="Return (%)", gridcolor="#1C2238"),
                    height=420,
                    margin=dict(l=40, r=20, t=20, b=40),
                )
                st.plotly_chart(fig_ef, use_container_width=True)

            with col2:
                st.markdown("#### Exact Allocation")
                fig_pie = go.Figure(
                    go.Pie(
                        labels=tickers,
                        values=[round(float(weights[t]) * 100, 2) for t in tickers],
                        hole=0.55,
                        marker=dict(
                            colors=["#F0B429", "#00D9A3", "#4B7CF3", "#FF4560", "#9B59B6", "#00B4D8"],
                            line=dict(color="#060810", width=3),
                        ),
                        textfont=dict(color="#E2E6F0"),
                    )
                )
                fig_pie.update_layout(
                    paper_bgcolor="#0C0F1A",
                    font=dict(color="#A8B3CC"),
                    height=420,
                    margin=dict(l=20, r=20, t=20, b=20),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("#### Asset Breakdown")
            table_data = []
            for ticker in tickers:
                avg_corr = (corr[ticker].sum() - 1) / (len(tickers) - 1)
                ticker_price = current_prices.loc[ticker]
                sharpe = (ann_ret[ticker] - risk_free) / ann_vol[ticker] if ann_vol[ticker] else 0.0
                table_data.append(
                    {
                        "Ticker": ticker,
                        "Exchange Symbol": ticker_price["Exchange Symbol"],
                        "Market": ticker_price["Market"],
                        "Current Price (INR)": format_inr(float(ticker_price["Price (INR)"])),
                        "Native Price": f"{ticker_price['Native Price']:.2f} {ticker_price['Native Currency']}",
                        "Weight (%)": round(float(weights[ticker]) * 100, 2),
                        "Exp. Return (%)": round(float(ann_ret[ticker]) * 100, 2),
                        "Volatility (%)": round(float(ann_vol[ticker]) * 100, 2),
                        "Sharpe": round(float(sharpe), 2),
                        "Max Drawdown (%)": round(float(dd_assets[ticker]) * 100, 2),
                        "Avg Correlation": round(float(avg_corr), 3),
                    }
                )

            st.dataframe(pd.DataFrame(table_data).set_index("Ticker"), use_container_width=True)

            comp_col, alloc_col = st.columns(2)
            with comp_col:
                st.markdown("#### Benchmark Comparison")
                fig_bench = go.Figure()
                for series_name, color in [
                    ("Portfolio", "#F0B429"),
                    ("NIFTY 50", "#00D9A3"),
                    ("S&P 500", "#4B7CF3"),
                ]:
                    fig_bench.add_trace(
                        go.Scatter(
                            x=benchmark_df.index,
                            y=(benchmark_df[series_name] - 1.0) * 100,
                            mode="lines",
                            line=dict(width=3, color=color),
                            name=series_name,
                        )
                    )
                fig_bench.update_layout(
                    paper_bgcolor="#0C0F1A",
                    plot_bgcolor="#0C0F1A",
                    font=dict(color="#A8B3CC"),
                    yaxis=dict(title="Return Since Start (%)", gridcolor="#1C2238"),
                    xaxis=dict(gridcolor="#1C2238"),
                    height=360,
                    margin=dict(l=40, r=20, t=20, b=40),
                )
                st.plotly_chart(fig_bench, use_container_width=True)
                st.dataframe(benchmark_stats.round(2), use_container_width=True)

            with alloc_col:
                st.markdown("#### Rupee Allocation")
                st.dataframe(allocation_df, use_container_width=True)
                st.download_button(
                    "Download PDF Report",
                    data=pdf_bytes,
                    file_name="portfolio_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            st.markdown("#### AI Commentary")
            st.info(commentary)

            st.markdown("#### Correlation Heatmap")
            fig_corr = go.Figure(
                go.Heatmap(
                    z=corr.values,
                    x=tickers,
                    y=tickers,
                    colorscale=[[0, "#4B7CF3"], [0.5, "#111521"], [1, "#F0B429"]],
                    text=corr.round(2).values,
                    texttemplate="%{text}",
                    zmin=-1,
                    zmax=1,
                )
            )
            fig_corr.update_layout(
                paper_bgcolor="#0C0F1A",
                font=dict(color="#A8B3CC"),
                height=350,
                margin=dict(l=40, r=20, t=20, b=40),
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        except Exception as exc:
            st.error(f"Could not complete the optimizer run: {exc}")

with watchlist_tab:
    st.markdown("### Watchlist")
    st.caption(
        "Track Indian and U.S. shares together. Indian symbols stay in INR, while foreign prices are converted to INR for comparison."
    )

    with st.form("add-watchlist-item", clear_on_submit=True):
        add_col1, add_col2, add_col3 = st.columns([2.2, 2.2, 1.2])
        with add_col1:
            new_symbol = st.text_input("Ticker", placeholder="BHEL or AAPL")
        with add_col2:
            new_market = st.selectbox("Market", options=["India (NSE)", "India (BSE)", "United States"])
        with add_col3:
            add_pressed = st.form_submit_button("Add Ticker", use_container_width=True)

    if add_pressed:
        cleaned_symbol = new_symbol.strip().upper()
        if not cleaned_symbol:
            st.warning("Enter a ticker before adding it to the watchlist.")
        else:
            exists = any(
                item["symbol"] == cleaned_symbol and item["market"] == new_market
                for item in st.session_state.watchlist
            )
            if exists:
                st.info("That ticker is already in your watchlist.")
            else:
                st.session_state.watchlist.append({"symbol": cleaned_symbol, "market": new_market})
                st.success(f"Added {cleaned_symbol} to the watchlist.")

    if st.session_state.watchlist:
        remove_options = [
            f"{item['symbol']} ({item['market']})" for item in st.session_state.watchlist
        ]
        remove_choice = st.selectbox("Remove ticker", options=["Keep all"] + remove_options)
        if st.button("Remove Selected", disabled=remove_choice == "Keep all"):
            chosen_label = remove_choice
            st.session_state.watchlist = [
                item
                for item in st.session_state.watchlist
                if f"{item['symbol']} ({item['market']})" != chosen_label
            ]
            st.success(f"Removed {chosen_label}.")

        entries = tuple((item["symbol"], item["market"]) for item in st.session_state.watchlist)
        try:
            with st.spinner("Fetching watchlist prices..."):
                watchlist_df = load_watchlist(entries)

            metric1, metric2, metric3 = st.columns(3)
            with metric1:
                st.metric("Tracked Shares", len(watchlist_df))
            with metric2:
                indian_count = int((watchlist_df["Native Currency"] == "INR").sum())
                st.metric("Indian Shares", indian_count)
            with metric3:
                avg_move = watchlist_df["Change (%)"].mean()
                st.metric("Average Daily Move", f"{avg_move:.2f}%")

            display_df = watchlist_df.copy()
            display_df["Native Price"] = display_df.apply(
                lambda row: f"{row['Native Price']:.2f} {row['Native Currency']}", axis=1
            )
            display_df["INR FX Rate"] = display_df["INR FX Rate"].map(lambda value: f"{value:,.4f}")
            display_df["Price (INR)"] = display_df["Price (INR)"].map(format_inr)
            display_df["Prev Close (INR)"] = display_df["Prev Close (INR)"].map(format_inr)
            display_df["Change (%)"] = display_df["Change (%)"].map(lambda value: f"{value:+.2f}%")
            display_df = display_df[
                [
                    "Ticker",
                    "Exchange Symbol",
                    "Market",
                    "Native Price",
                    "Price (INR)",
                    "Prev Close (INR)",
                    "Change (%)",
                    "INR FX Rate",
                ]
            ]

            st.dataframe(display_df, use_container_width=True)
            st.caption(
                "Example: BHEL stays around its actual rupee price, while AAPL is shown in INR after conversion."
            )
        except Exception as exc:
            st.error(f"Could not load the watchlist: {exc}")
    else:
        st.info("Add a ticker to start tracking your watchlist.")
