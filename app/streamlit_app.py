import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # project root
sys.path.append(str(ROOT))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.data.finnhub import get_quote
from src.data.yahoo import get_candles_yahoo
from src.strategies.buy_hold import buy_and_hold
from src.strategies.momentum import momentum_strategy
from src.metrics.performance import compute_metrics


st.set_page_config(page_title="Quant A - Single Asset Dashboard", layout="wide")

st.title("Quant Finance Dashboard — Quant A (Single Asset)")

# Sidebar controls
st.sidebar.header("Controls")

asset = st.sidebar.selectbox("Asset", options=["AAPL"], index=0)
interval = st.sidebar.selectbox("Data interval (Yahoo)", options=["5m", "15m", "30m", "60m"], index=0)
period = st.sidebar.selectbox("History window (Yahoo)", options=["5d", "1mo", "2mo"], index=0)

strategy = st.sidebar.selectbox("Strategy", options=["Buy & Hold", "Momentum"], index=0)

lookback = 20
if strategy == "Momentum":
    lookback = st.sidebar.slider("Lookback (periods)", min_value=5, max_value=200, value=20, step=5)

initial_value = st.sidebar.number_input(
    "Initial portfolio value",
    min_value=10.0,
    max_value=1_000_000.0,
    value=100.0,
    step=10.0,
)

st.sidebar.caption("Refresh: quote every run; data cached for performance.")

# Data loading
@st.cache_data(ttl=300)  # 5 minutes
def load_prices(symbol: str, interval: str, period: str) -> pd.DataFrame:
    return get_candles_yahoo(symbol, interval=interval, period=period)


# Header: current quote
colA, colB, colC, colD = st.columns(4)

try:
    q = get_quote(asset)
    last = q.get("c", None)
    dp = q.get("dp", None)
    colA.metric(
        f"{asset} last price (Finnhub)",
        f"{last:.2f}" if last is not None else "N/A",
        f"{dp:.2f}%" if dp is not None else None,
    )
except Exception as e:
    colA.warning(f"Finnhub quote unavailable: {e}")

prices = load_prices(asset, interval, period)

# Strategy computation
if strategy == "Buy & Hold":
    out = buy_and_hold(prices, initial_value=float(initial_value))
    equity_col = "equity_bh"
    ret_col = "ret"
else:
    out = momentum_strategy(prices, lookback=int(lookback), initial_value=float(initial_value))
    equity_col = "equity_mom"
    ret_col = "strat_ret"

m = compute_metrics(out, equity_col=equity_col, ret_col=ret_col)

# Metrics display
colB.metric("Total return", f"{m['total_return']*100:.2f}%")
colC.metric("Volatility (ann.)", f"{m['volatility']*100:.2f}%")
colD.metric("Max drawdown", f"{m['max_drawdown']*100:.2f}%")
st.metric("Sharpe (ann.)", f"{m['sharpe']:.2f}")

# Main chart: price + equity curve
fig = go.Figure()
fig.add_trace(go.Scatter(x=out["timestamp"], y=out["close"], name="Price", yaxis="y1"))
fig.add_trace(go.Scatter(x=out["timestamp"], y=out[equity_col], name="Strategy equity", yaxis="y2"))

title = f"{asset} — Price vs Strategy Equity ({strategy})"
if strategy == "Momentum":
    title += f" | lookback={lookback}"

fig.update_layout(
    title=title,
    xaxis_title="Time",
    yaxis=dict(title="Price"),
    yaxis2=dict(title="Equity", overlaying="y", side="right"),
    legend=dict(orientation="h"),
)

st.plotly_chart(fig, width="stretch")

# Momentum signal
if strategy == "Momentum" and "signal_lag" in out.columns:
    st.subheader(f"Momentum signal (lagged) — resampled (lookback={lookback})")

    sig = out[["timestamp", "signal_lag"]].copy()
    sig = sig.set_index("timestamp").sort_index()

    # Resample to reduce noise (choose 15T or 30T)
    sig_rs = sig["signal_lag"].resample("30T").last().dropna()

    fig_sig = go.Figure()
    fig_sig.add_trace(
        go.Scatter(
            x=sig_rs.index,
            y=sig_rs.values,
            mode="lines",
            line_shape="hv",
            name="signal",
        )
    )
    fig_sig.update_layout(
    xaxis_title="Time",
    yaxis_title="Signal (0/1)",
    yaxis=dict(range=[-0.05, 1.05]),
    showlegend=False,
)
    fig_sig.update_yaxes(tickmode="array", tickvals=[0, 1])

    st.plotly_chart(fig_sig, width="stretch")

    invested_pct = out["signal_lag"].mean() * 100
    st.caption(f"Invested {invested_pct:.1f}% of the time")

# Show raw data
with st.expander("Show data"):
    st.dataframe(out.tail(50))

