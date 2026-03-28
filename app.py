# app.py

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(__file__))

from data.fetcher   import fetch_prices
from mpt.returns    import compute_returns, annualized_returns, annualized_volatility, covariance_matrix, correlation_matrix
from mpt.montecarlo import run_monte_carlo, get_optimal_portfolios, get_weights
from charts.plotter import plot_efficient_frontier, plot_allocation_pie

import plotly.graph_objects as go
import pandas as pd

# ── Page config ──
st.set_page_config(
    page_title="Portfolio Optimizer",
    page_icon="📈",
    layout="wide"
)

# ── Custom CSS ──
st.markdown("""
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
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("## 📈 Stock Portfolio Optimizer")
st.markdown("*Modern Portfolio Theory · Efficient Frontier · Monte Carlo Simulation*")
st.divider()

# ── Sidebar ──
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    raw_input = st.text_input(
        "Tickers (comma-separated)",
        value="AAPL, MSFT, GOOGL, AMZN, NVDA"
    )
    tickers = [t.strip().upper() for t in raw_input.split(",") if t.strip()]

    risk_free = st.slider(
        "Risk-Free Rate (%)", 
        min_value=0.0, max_value=10.0, value=4.3, step=0.1
    ) / 100

    n_sims = st.selectbox(
        "Monte Carlo Simulations",
        options=[1_000, 5_000, 10_000, 20_000],
        index=2
    )

    run = st.button("🚀 Run Analysis", use_container_width=True)

    st.divider()
    st.markdown("**How it works:**")
    st.markdown("""
    1. Fetches 12 months of price data
    2. Computes returns & covariance
    3. Runs Monte Carlo simulations
    4. Finds Max Sharpe portfolio
    5. Plots the efficient frontier
    """)

# ── Main ──
if not run:
    st.info("👈 Add your tickers in the sidebar and click **Run Analysis**")
    st.stop()

if len(tickers) < 2:
    st.error("Please enter at least 2 tickers.")
    st.stop()

# ── Run pipeline ──
with st.spinner("Fetching price data..."):
    prices = fetch_prices(tickers)

with st.spinner("Computing returns & covariance..."):
    returns  = compute_returns(prices)
    ann_ret  = annualized_returns(returns)
    ann_vol  = annualized_volatility(returns)
    cov      = covariance_matrix(returns)
    corr     = correlation_matrix(returns)

with st.spinner(f"Running {n_sims:,} Monte Carlo simulations..."):
    mc_df   = run_monte_carlo(ann_ret, cov, risk_free_rate=risk_free, n_simulations=n_sims)
    optimal = get_optimal_portfolios(mc_df)
    ms      = optimal["max_sharpe"]
    mv      = optimal["min_vol"]

st.success("✅ Analysis complete!")
st.divider()

# ── Metric Cards ──
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Max Sharpe Ratio</div>
        <div class="metric-value gold">{ms['sharpe']:.2f}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Expected Return</div>
        <div class="metric-value green">{ms['return']*100:.1f}%</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Portfolio Volatility</div>
        <div class="metric-value blue">{ms['volatility']*100:.1f}%</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Min-Vol Return</div>
        <div class="metric-value">{mv['return']*100:.1f}%</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── Charts ──
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown("#### Efficient Frontier")
    fig_ef = go.Figure()
    fig_ef.add_trace(go.Scatter(
        x=mc_df["volatility"]*100, y=mc_df["return"]*100,
        mode="markers",
        marker=dict(size=3, color=mc_df["sharpe"],
                    colorscale=[[0,"#4B7CF3"],[0.5,"#00D9A3"],[1,"#F0B429"]],
                    colorbar=dict(title="Sharpe"), opacity=0.5),
        name="Portfolios"
    ))
    fig_ef.add_trace(go.Scatter(
        x=[ms["volatility"]*100], y=[ms["return"]*100],
        mode="markers+text", marker=dict(size=15, color="#F0B429", symbol="star"),
        text=["Max Sharpe"], textposition="top center",
        textfont=dict(color="#F0B429"), name="Max Sharpe"
    ))
    fig_ef.add_trace(go.Scatter(
        x=[mv["volatility"]*100], y=[mv["return"]*100],
        mode="markers+text", marker=dict(size=13, color="#00D9A3", symbol="triangle-up"),
        text=["Min Vol"], textposition="top center",
        textfont=dict(color="#00D9A3"), name="Min Vol"
    ))
    fig_ef.update_layout(
        paper_bgcolor="#0C0F1A", plot_bgcolor="#0C0F1A",
        font=dict(color="#A8B3CC"),
        xaxis=dict(title="Volatility (%)", gridcolor="#1C2238"),
        yaxis=dict(title="Return (%)", gridcolor="#1C2238"),
        height=420, margin=dict(l=40,r=20,t=20,b=40)
    )
    st.plotly_chart(fig_ef, use_container_width=True)

with col2:
    st.markdown("#### Optimal Allocation")
    weights = [ms[t] for t in tickers]
    colors  = ["#F0B429","#00D9A3","#4B7CF3","#FF4560","#9B59B6",
               "#00B4D8","#F72585","#06D6A0","#FFB703","#3A86FF"]
    fig_pie = go.Figure(go.Pie(
        labels=tickers, values=[round(w*100,2) for w in weights],
        hole=0.55, marker=dict(colors=colors[:len(tickers)],
        line=dict(color="#060810", width=3)),
        textfont=dict(color="#E2E6F0")
    ))
    fig_pie.update_layout(
        paper_bgcolor="#0C0F1A", font=dict(color="#A8B3CC"),
        height=420, margin=dict(l=20,r=20,t=20,b=20)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Asset Table ──
st.markdown("#### Asset Breakdown")
table_data = []
for i, t in enumerate(tickers):
    avg_corr = (corr[t].sum() - 1) / (len(tickers) - 1)
    table_data.append({
        "Ticker":          t,
        "Weight (%)":      round(ms[t] * 100, 1),
        "Exp. Return (%)": round(ann_ret[t] * 100, 1),
        "Volatility (%)":  round(ann_vol[t] * 100, 1),
        "Sharpe":          round((ann_ret[t] - risk_free) / ann_vol[t], 2),
        "Avg Correlation": round(avg_corr, 3)
    })

st.dataframe(
    pd.DataFrame(table_data).set_index("Ticker"),
    use_container_width=True
)

# ── Correlation Heatmap ──
st.markdown("#### Correlation Heatmap")
fig_corr = go.Figure(go.Heatmap(
    z=corr.values, x=tickers, y=tickers,
    colorscale=[[0,"#4B7CF3"],[0.5,"#111521"],[1,"#F0B429"]],
    text=corr.round(2).values, texttemplate="%{text}",
    zmin=-1, zmax=1
))
fig_corr.update_layout(
    paper_bgcolor="#0C0F1A", font=dict(color="#A8B3CC"),
    height=350, margin=dict(l=40,r=20,t=20,b=40)
)
st.plotly_chart(fig_corr, use_container_width=True)