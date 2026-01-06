import sys
from pathlib import Path

# Add project root to system path to allow importing from 'src'
# This is required because app_quant_b.py is inside the 'app' folder
ROOT = Path(__file__).resolve().parents[1]
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

# Page configuration
st.set_page_config(page_title="Quant B - Portfolio Manager", layout="wide")

st.title("Quant B - Multi-Asset Portfolio Manager")

# --- SIDEBAR: CONTROLS ---
st.sidebar.header("Portfolio Settings")

# Define available assets for the simulation
# In a real app, this could be a text input, but fixed list is safer for demo
assets = ["AAPL", "MSFT", "KO", "JPM"]
selected_assets = st.sidebar.multiselect("Select Assets (min 3)", assets, default=["AAPL", "MSFT", "KO"])

# Dynamic sliders for weights
weights = {}
st.sidebar.subheader("Asset Allocation")
for asset in selected_assets:
    # Default weight is equal weight
    weights[asset] = st.sidebar.slider(f"Weight: {asset}", 0.0, 1.0, 1.0/len(selected_assets))

# Button to trigger simulation
run_btn = st.sidebar.button("Run Simulation")

# --- MAIN LOGIC ---
if run_btn or selected_assets:
    if len(selected_assets) < 3:
        st.error("Please select at least 3 assets to satisfy Quant B requirements.")
    else:
        # Load data with caching to improve performance
        @st.cache_data
        @st.cache_data
        @st.cache_data
        def load_data(tickers):
            data = {}
            for t in tickers:
                try:
                    df = get_candles_yahoo(t, period="1y", interval="1d")
                    if not df.empty:
                        data[t] = df.set_index("timestamp")["close"]
                except Exception as e:
                    # Message in English to avoid encoding errors (0xe9)
                    st.warning(f"Warning: Could not load data for {t}. ({e})")
            
            return pd.DataFrame(data).dropna()

        st.info(f"Fetching data for: {', '.join(selected_assets)}...")
        df_prices = load_data(selected_assets)

        if not df_prices.empty:
            # 1. Compute Portfolio Strategy
            port_results = compute_portfolio_equity(df_prices, weights)
            
            # 2. Compute Risk Metrics
            corr_matrix, vol_metrics = compute_risk_metrics(df_prices, weights)

            # --- DISPLAY: VISUAL COMPARISON ---
            st.subheader("Performance Comparison: Assets vs Portfolio")
            
            # Normalize prices to base 100 for valid visual comparison
            norm_prices = (df_prices / df_prices.iloc[0]) * 100
            
            fig = go.Figure()
            
            # Plot individual assets (faded lines)
            for asset in selected_assets:
                fig.add_trace(go.Scatter(
                    x=norm_prices.index, 
                    y=norm_prices[asset], 
                    name=asset,
                    opacity=0.5
                ))
            
            # Plot Portfolio (Strong black line)
            fig.add_trace(go.Scatter(
                x=port_results.index, 
                y=port_results["equity_curve"], 
                name="PORTFOLIO",
                line=dict(color='black', width=4)
            ))
            
            fig.update_layout(xaxis_title="Date", yaxis_title="Normalized Value (Base 100)")
            st.plotly_chart(fig, use_container_width=True)

            # --- DISPLAY: METRICS & RISK ---
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Risk Analysis (Volatility)")
                # Display table showing Portfolio Vol vs Individual Vols
                st.dataframe(vol_metrics.style.format("{:.2%}"))
                
                # Calculate Diversification Benefit
                avg_asset_vol = vol_metrics.loc[selected_assets, "Volatility"].mean()
                port_vol = vol_metrics.loc["PORTFOLIO", "Volatility"]
                div_effect = avg_asset_vol - port_vol
                
                st.success(f"Diversification Effect: Your portfolio volatility is {div_effect*100:.2f}% lower than the average asset volatility.")

            with col2:
                st.subheader("Correlation Matrix")
                # Heatmap visualization
                fig_corr = px.imshow(
                    corr_matrix, 
                    text_auto=".2f", 
                    color_continuous_scale='RdBu_r', 
                    zmin=-1, zmax=1
                )
                st.plotly_chart(fig_corr, use_container_width=True)

        else:
            st.error("No data found. Please check your internet connection or ticker symbols.")