import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from streamlit_autorefresh import st_autorefresh

from src.data.finnhub import get_quote as raw_get_quote
from src.data.yahoo import get_candles_yahoo as raw_get_candles_yahoo
from src.strategies.buy_hold import buy_and_hold
from src.strategies.momentum import momentum_strategy
from src.metrics.performance import compute_metrics



# App config

st.set_page_config(
    page_title="Quant Dashboard — Single Asset",
    page_icon="📈",
    layout="wide",
)
def load_css():
    css_path = ROOT / ".streamlit" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

load_css()


# Auto refresh every 5 minutes
st_autorefresh(interval=5 * 60 * 1000, key="auto_refresh_5min")

PARIS_NOW = datetime.now(ZoneInfo("Europe/Paris"))


# Cached data fetch wrappers
@st.cache_data(ttl=300)
def get_quote(symbol: str):
    return raw_get_quote(symbol)


@st.cache_data(ttl=300)
def get_candles_yahoo(symbol: str, interval: str, period: str) -> pd.DataFrame:
    return raw_get_candles_yahoo(symbol, interval=interval, period=period)


def load_prices(symbol: str, interval: str, period: str) -> pd.DataFrame:
    return get_candles_yahoo(symbol, interval=interval, period=period)


def format_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


# Header
st.markdown(
    """
    <div style="display:flex; align-items:flex-end; justify-content:space-between; gap:12px;">
      <div>
        <h1 style="margin-bottom:0;">📈 Quant Finance Dashboard</h1>
        <p style="margin-top:4px; color: #6b7280;">
          Quant A — Single Asset • Real-time quote (Finnhub) + Intraday candles (Yahoo)
        </p>
      </div>
      <div style="text-align:right; color:#6b7280;">
        <div><b>Last updated (Paris)</b></div>
        <div>{}</div>
        <div style="margin-top:6px; font-size:12px;">
          Auto-refresh: <b>5 min</b> • Cache TTL: <b>300s</b>
        </div>
      </div>
    </div>
    <hr style="margin-top:10px; margin-bottom:15px;" />
    """.format(PARIS_NOW.strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True,
)


# Sidebar controls
with st.sidebar:
    st.header("⚙️ Controls")

    st.subheader("Asset & Data")
    asset = st.selectbox("Asset", options=["AAPL"], index=0)
    interval = st.selectbox("Intraday interval (Yahoo)", options=["5m", "15m", "30m", "60m"], index=0)
    period = st.selectbox("History window (Yahoo)", options=["5d", "1mo", "2mo"], index=0)

    st.subheader("Strategy")
    strategy = st.selectbox("Strategy", options=["Buy & Hold", "Momentum"], index=0)

    lookback = 20
    if strategy == "Momentum":
        lookback = st.slider("Momentum lookback (periods)", min_value=5, max_value=200, value=20, step=5, key="lookback")

    st.subheader("Portfolio")
    initial_value = st.number_input(
        "Initial portfolio value",
        min_value=10.0,
        max_value=1_000_000.0,
        value=100.0,
        step=10.0,
    )

    st.info("Auto-refresh every 5 minutes.\n\nData fetches are cached for 300s to avoid API spamming.")



# Top KPIs: Quote + performance

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns([1.2, 1, 1, 1, 1])
# Quote KPI
last = None
dp = None
try:
    q = get_quote(asset)
    last = q.get("c", None)
    dp = q.get("dp", None)
    kpi1.metric(
        f"{asset} (Finnhub)",
        f"{last:.2f}" if last is not None else "N/A",
        f"{dp:.2f}%" if dp is not None else None,
    )
except Exception as e:
    kpi1.warning(f"Finnhub quote unavailable: {e}")

# Load prices
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

# Performance KPIs
kpi2.metric("Total return", format_pct(m["total_return"]))
kpi3.metric("Volatility (ann.)", format_pct(m["volatility"]))
kpi4.metric("Max drawdown", format_pct(m["max_drawdown"]))
kpi5.metric("Sharpe (ann.)", f"{m['sharpe']:.2f}")


# Tabs

tab_overview, tab_strategy, tab_data = st.tabs(["📊 Overview", "🧠 Strategy", "🗃️ Data"])

with tab_overview:
    st.subheader("Price vs Strategy Equity")

    title = f"{asset} — Price vs Strategy Equity ({strategy})"
    if strategy == "Momentum":
        title += f" • lookback={lookback}"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=out["timestamp"],
            y=out["close"],
            name="Price",
            yaxis="y1",
            mode="lines",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=out["timestamp"],
            y=out[equity_col],
            name="Strategy equity",
            yaxis="y2",
            mode="lines",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis=dict(title="Price"),
        yaxis2=dict(title="Equity", overlaying="y", side="right"),
        legend=dict(orientation="h"),
        hovermode="x unified",
        margin=dict(l=30, r=30, t=60, b=30),
    )

    # Nice range selector
    fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1D", step="day", stepmode="backward"),
                    dict(count=5, label="5D", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            )
        ),
    )

    st.plotly_chart(fig, width="stretch")

    # Quick context line
    st.caption(
        f"Data: Yahoo intraday ({interval}, {period}). Strategy: {strategy}. "
        f"Auto-refresh 5 min, cache TTL 300s."
    )

with tab_strategy:
    st.subheader("Strategy Details")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Selected strategy**")
        st.write(f"- Strategy: **{strategy}**")
        if strategy == "Momentum":
            st.write(f"- Lookback: **{lookback}** periods")
        st.write(f"- Initial value: **{float(initial_value):,.2f}**")

    with c2:
        st.markdown("**Data frequency**")
        st.write(f"- Interval: **{interval}**")
        st.write(f"- History window: **{period}**")
        st.write(f"- Rows loaded: **{len(prices):,}**")

    if strategy == "Momentum" and "signal_lag" in out.columns:
        st.divider()
        st.subheader("Momentum signal (lagged) — resampled")

        sig = out[["timestamp", "signal_lag"]].copy()
        sig = sig.set_index("timestamp").sort_index()

        # Replace deprecated "T" by "min"
        sig_rs = sig["signal_lag"].resample("30min").last().dropna()

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
            hovermode="x unified",
            showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30),
        )
        fig_sig.update_yaxes(tickmode="array", tickvals=[0, 1])

        st.plotly_chart(fig_sig, width="stretch")

        invested_pct = out["signal_lag"].mean() * 100
        st.caption(f"Invested **{invested_pct:.1f}%** of the time (based on lagged signal).")

    st.divider()
    st.subheader("Download backtest output")
    csv_bytes = out.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download backtest CSV",
        data=csv_bytes,
        file_name=f"{asset}_{interval}_{period}_{strategy.replace(' ', '_')}.csv",
        mime="text/csv",
    )

with tab_data:
    st.subheader("Raw data preview")

    st.write("**Prices (Yahoo intraday)**")
    st.dataframe(prices.tail(50), use_container_width=True)

    st.write("**Backtest output**")
    st.dataframe(out.tail(50), use_container_width=True)

    st.caption(
        "Note: Yahoo intraday data can sometimes have missing bars. "
        "Caching reduces repeated API calls."
    )


