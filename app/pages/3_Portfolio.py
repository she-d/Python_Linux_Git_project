import sys
from pathlib import Path

# Add project root to system path to allow importing from 'src'
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Import your custom modules
from src.data.yahoo import get_candles_yahoo
from src.strategies.portfolio_allocation import compute_portfolio_equity
from src.metrics.risk_analysis import compute_risk_metrics

# Page title (avoid set_page_config here if it's already set in main app)
st.title("Quant B - Multi-Asset Portfolio Manager")

# SIDEBAR: CONTROLS 
st.sidebar.header("Portfolio Settings")

assets = ["AAPL", "MSFT", "KO", "JPM"]
selected_assets = st.sidebar.multiselect(
    "Select Assets (min 3)", assets, default=["AAPL", "MSFT", "KO"]
)

# Dynamic sliders for weights
weights = {}
st.sidebar.subheader("Asset Allocation")
for asset in selected_assets:
    weights[asset] = st.sidebar.slider(
        f"Weight: {asset}",
        0.0,
        1.0,
        1.0 / len(selected_assets) if len(selected_assets) > 0 else 0.0,
        key=f"w_{asset}",
    )

# Normalize weights to sum to 1 (important for portfolio math)
w_sum = sum(weights.values())
if len(selected_assets) > 0:
    if w_sum > 0:
        weights = {k: v / w_sum for k, v in weights.items()}
    else:
        weights = {k: 1.0 / len(selected_assets) for k in selected_assets}

run_btn = st.sidebar.button("Run Simulation")

# DATA LOADING (robust + debug)
@st.cache_data(ttl=300)
def load_data(tickers):
    data = {}
    errors = {}

    for t in tickers:
        try:
            df = get_candles_yahoo(t, period="1y", interval="1d")

            if df is None or df.empty:
                errors[t] = "empty dataframe"
                continue

            if "timestamp" not in df.columns or "close" not in df.columns:
                errors[t] = f"missing columns: {list(df.columns)}"
                continue

            s = df.set_index("timestamp")["close"].dropna()
            if s.empty:
                errors[t] = "close series empty after dropna"
                continue

            data[t] = s

        except Exception as e:
            errors[t] = str(e)

    prices = pd.DataFrame(data).dropna()
    return prices, errors


# MAIN LOGIC 
if run_btn or selected_assets:
    if len(selected_assets) < 3:
        st.error("Please select at least 3 assets to satisfy Quant B requirements.")
        st.stop()

    st.info(f"Fetching data for: {', '.join(selected_assets)}...")
    df_prices, errors = load_data(selected_assets)

    if errors:
        with st.expander("Data load debug (click to expand)"):
            st.write(errors)
            st.write("Loaded columns:", list(df_prices.columns))
            st.write("Rows:", len(df_prices))

    if df_prices.empty:
        st.error("No data found. Please check your internet connection or ticker symbols.")
        st.stop()

    # 1) Compute Portfolio Strategy
    port_results = compute_portfolio_equity(df_prices, weights)

    # 2) Compute Risk Metrics
    corr_matrix, vol_metrics = compute_risk_metrics(df_prices, weights)

    #DISPLAY: VISUAL COMPARISON 
    st.subheader("Performance Comparison: Assets vs Portfolio")

    # Normalize prices to base 100 for valid visual comparison
    norm_prices = (df_prices / df_prices.iloc[0]) * 100

    fig = go.Figure()

    # Plot individual assets (faded lines)
    for asset in selected_assets:
        if asset in norm_prices.columns:
            fig.add_trace(
                go.Scatter(
                    x=norm_prices.index,
                    y=norm_prices[asset],
                    name=asset,
                    opacity=0.5,
                )
            )

    # Plot Portfolio (strong line)
    fig.add_trace(
        go.Scatter(
            x=port_results.index,
            y=port_results["equity_curve"],
            name="PORTFOLIO",
            line=dict(color="black", width=4),
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Normalized Value (Base 100)",
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig, use_container_width=True)

    #DISPLAY: METRICS & RISK 
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Analysis (Volatility)")
        st.dataframe(vol_metrics.style.format("{:.2%}"))

        # Diversification effect (safe checks)
        try:
            avg_asset_vol = vol_metrics.loc[selected_assets, "Volatility"].mean()
            port_vol = vol_metrics.loc["PORTFOLIO", "Volatility"]
            div_effect = avg_asset_vol - port_vol
            st.success(
                f"Diversification Effect: Your portfolio volatility is {div_effect*100:.2f}% "
                f"lower than the average asset volatility."
            )
        except Exception:
            st.info("Diversification effect unavailable (check vol_metrics index/columns).")

    with col2:
        st.subheader("Correlation Matrix")
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
        )
        st.plotly_chart(fig_corr, use_container_width=True)