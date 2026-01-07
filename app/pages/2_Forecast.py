from pathlib import Path
import sys

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.models.linear_forecast import forecast_next_day_ols_from_daily  # noqa: E402


st.set_page_config(page_title="Forecast", layout="wide")
st_autorefresh(interval=5 * 60 * 1000, key="auto_refresh_5min")


st.title("Forecast (Baseline Linear Regression)")
st.caption("Daily next-day forecast with 95% prediction interval (OLS).")

csv_path = ROOT / "data" / "aapl_daily.csv"

with st.sidebar:
    st.header("Forecast settings")
    lags = st.slider("Return lags", 2, 20, 5, 1)
    vol_window = st.slider("Volatility window (days)", 5, 60, 10, 1)
    momentum_lookback = st.slider("Momentum lookback (days)", 5, 120, 10, 1)
    ci = st.selectbox("Prediction interval", ["90%", "95%", "99%"], index=1)
    hist_days = st.slider("History shown (days)", 30, 400, 120, 10)
    st.caption("Last updated (Paris): " + datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S"))

alpha_map = {"90%": 0.10, "95%": 0.05, "99%": 0.01}
alpha = alpha_map[ci]

if not csv_path.exists():
    st.error(f"Missing {csv_path}. Run: python scripts/fetch_daily_yahoo.py")
    st.stop()

df_daily = pd.read_csv(csv_path)
df_daily["date"] = pd.to_datetime(df_daily["date"], errors="coerce")
df_daily["close"] = pd.to_numeric(df_daily["close"], errors="coerce")

df_daily = df_daily.dropna(subset=["date", "close"]).sort_values("date")

# Run forecast
res = forecast_next_day_ols_from_daily(
    df_daily=df_daily,
    date_col="date",
    close_col="close",
    lags=lags,
    vol_window=vol_window,
    momentum_lookback=momentum_lookback,
    alpha=alpha,
    min_train_rows=60,
)

# Display key numbers
c1, c2, c3, c4 = st.columns(4)
c1.metric("As of (last daily close)", res.as_of_date)
c2.metric("Last close", f"{res.last_close:.2f}")
c3.metric("Pred next close", f"{res.pred_close:.2f}")
c4.metric(f"PI {ci}", f"[{res.lower_close:.2f}, {res.upper_close:.2f}]")

st.write("")
st.caption(
    f"Train rows: {res.n_train} • R²(train): {res.model_r2:.4f} (baseline models often have low R² on returns)"
)

# Prepare plot data
df_plot = df_daily.copy()
df_plot = df_plot.set_index("date")
df_plot = df_plot.tail(hist_days)

as_of_dt = pd.to_datetime(res.as_of_date)
forecast_dt = as_of_dt + pd.Timedelta(days=1)

# Plot
fig, ax = plt.subplots(figsize=(10, 4))


ax.plot(df_plot.index, df_plot["close"].values, label="Daily close")

# forecast point + interval "band" (vertical line / marker)
ax.scatter([forecast_dt], [res.pred_close], label="Forecast", marker="o")
ax.vlines(forecast_dt, res.lower_close, res.upper_close, label=f"Prediction interval {ci}")

ax.set_title("Daily close with next-day forecast + prediction interval")
ax.set_xlabel("Date")
ax.set_ylabel("Price")
ax.legend()

fig.tight_layout()
st.pyplot(fig, use_container_width=True)

plt.close(fig)
