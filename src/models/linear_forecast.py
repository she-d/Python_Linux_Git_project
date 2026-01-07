from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass
class ForecastResult:
    as_of_date: str
    last_close: float

    pred_return: float
    lower_return: float
    upper_return: float

    pred_close: float
    lower_close: float
    upper_close: float

    n_train: int
    model_r2: Optional[float] = None


def _ensure_datetime_index(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """
    Ensure a DatetimeIndex exists. Accepts either:
      - a column named `timestamp_col`, or
      - an existing DatetimeIndex
    """
    out = df.copy()

    if isinstance(out.index, pd.DatetimeIndex):
        out = out.sort_index()
        return out

    if timestamp_col not in out.columns:
        raise ValueError(
            f"Missing datetime index and missing '{timestamp_col}' column. "
            f"Available columns: {list(out.columns)}"
        )

    out[timestamp_col] = pd.to_datetime(out[timestamp_col], utc=False, errors="coerce")
    out = out.dropna(subset=[timestamp_col]).set_index(timestamp_col).sort_index()
    return out


def intraday_to_daily_close(df_intraday: pd.DataFrame, close_col: str = "close") -> pd.Series:
    """
    Convert intraday candles to daily closes (last close of each calendar day).
    """
    df = _ensure_datetime_index(df_intraday)

    if close_col not in df.columns:
        raise ValueError(f"Missing '{close_col}' column. Available: {list(df.columns)}")

    daily_close = df[close_col].resample("1D").last().dropna()
    daily_close.name = "close"
    return daily_close


def build_daily_features_and_target(
    daily_close: pd.Series,
    lags: int = 5,
    vol_window: int = 10,
    momentum_lookback: int = 10,
    horizon_days: int = 1,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Features at time t (no look-ahead), target is future log return over `horizon_days`.
    y_t = log(close_{t+h} / close_t)
    """
    close = daily_close.astype(float).copy()
    close = close.dropna()
    if close.size < 30:
        raise ValueError(f"Not enough daily points ({close.size}). Need ~60+ for decent intervals.")

    r = np.log(close / close.shift(1))
    # Target: future log-return
    y = np.log(close.shift(-horizon_days) / close)

    X = pd.DataFrame(index=close.index)
    # Lagged returns (use only past info)
    for k in range(1, lags + 1):
        X[f"r_lag_{k}"] = r.shift(k)

    # Rolling vol (use only past info: shift by 1)
    X["vol"] = r.rolling(vol_window).std().shift(1)

    # Momentum (based on past close)
    X["mom"] = (close / close.shift(momentum_lookback) - 1.0)

    # Align and drop NaNs for training rows
    return X, y


def forecast_next_day_ols(
    df_intraday: pd.DataFrame,
    close_col: str = "close",
    timestamp_col: str = "timestamp",
    lags: int = 5,
    vol_window: int = 10,
    momentum_lookback: int = 10,
    alpha: float = 0.05,
    min_train_rows: int = 40,
) -> ForecastResult:
    """
    Forecast next-day close using OLS on daily features.
    Uses statsmodels prediction interval (obs_ci_lower/upper).
    """
    # 1) Daily close series
    df_intraday = _ensure_datetime_index(df_intraday, timestamp_col=timestamp_col)
    daily_close = intraday_to_daily_close(df_intraday, close_col=close_col)

    # 2) Features & target
    X_all, y_all = build_daily_features_and_target(
        daily_close,
        lags=lags,
        vol_window=vol_window,
        momentum_lookback=momentum_lookback,
        horizon_days=1,
    )

    # Last feature row we want to predict from (typically the last available day)
    X_last = X_all.dropna().iloc[-1:]
    as_of_date = X_last.index[-1].date().isoformat()
    last_close = float(daily_close.loc[X_last.index[-1]])

    # Training data: rows where both X and y are defined
    train_mask = X_all.notna().all(axis=1) & y_all.notna()
    X_train = X_all.loc[train_mask]
    y_train = y_all.loc[train_mask]

    if len(X_train) < min_train_rows:
        raise ValueError(
            f"Not enough training rows ({len(X_train)}). "
            f"Try increasing history (daily) or reducing lags/windows."
        )

    # 3) Fit OLS
    X_train_c = sm.add_constant(X_train, has_constant="add")
    model = sm.OLS(y_train, X_train_c).fit()

    # 4) Predict with prediction interval
    X_last_c = sm.add_constant(X_last, has_constant="add")
    pred = model.get_prediction(X_last_c)
    frame = pred.summary_frame(alpha=alpha)

    mean = float(frame["mean"].iloc[0])
    lower_r = float(frame["obs_ci_lower"].iloc[0])
    upper_r = float(frame["obs_ci_upper"].iloc[0])

    pred_close = last_close * float(np.exp(mean))
    lower_close = last_close * float(np.exp(lower_r))
    upper_close = last_close * float(np.exp(upper_r))

    return ForecastResult(
        as_of_date=as_of_date,
        last_close=last_close,
        pred_return=mean,
        lower_return=lower_r,
        upper_return=upper_r,
        pred_close=pred_close,
        lower_close=lower_close,
        upper_close=upper_close,
        n_train=len(X_train),
        model_r2=float(model.rsquared) if model.rsquared is not None else None,
    )
def daily_df_to_close_series(
    df_daily: pd.DataFrame,
    date_col: str = "date",
    close_col: str = "close",
) -> pd.Series:
    """
    Accepts a daily DataFrame with columns like [date, close] and returns
    a daily close Series with a DatetimeIndex.
    """
    df = df_daily.copy()

    if isinstance(df.index, pd.DatetimeIndex) and close_col in df.columns:
        s = df[close_col].astype(float).sort_index().dropna()
        s.name = "close"
        return s

    if date_col not in df.columns or close_col not in df.columns:
        raise ValueError(f"Daily DF must contain '{date_col}' and '{close_col}'. Got {list(df.columns)}")

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, close_col]).sort_values(date_col)
    s = df.set_index(date_col)[close_col].astype(float)
    s = s[~s.index.duplicated(keep="last")].sort_index().dropna()
    s.name = "close"
    return s


def forecast_next_day_ols_from_daily(
    df_daily: pd.DataFrame,
    date_col: str = "date",
    close_col: str = "close",
    lags: int = 5,
    vol_window: int = 10,
    momentum_lookback: int = 10,
    alpha: float = 0.05,
    min_train_rows: int = 60,
) -> ForecastResult:
    """
    Same model as forecast_next_day_ols but uses daily close data directly.
    """
    daily_close = daily_df_to_close_series(df_daily, date_col=date_col, close_col=close_col)

    X_all, y_all = build_daily_features_and_target(
        daily_close,
        lags=lags,
        vol_window=vol_window,
        momentum_lookback=momentum_lookback,
        horizon_days=1,
    )

    X_last = X_all.dropna().iloc[-1:]
    as_of_date = X_last.index[-1].date().isoformat()
    last_close = float(daily_close.loc[X_last.index[-1]])

    train_mask = X_all.notna().all(axis=1) & y_all.notna()
    X_train = X_all.loc[train_mask]
    y_train = y_all.loc[train_mask]

    if len(X_train) < min_train_rows:
        raise ValueError(
            f"Not enough training rows ({len(X_train)}). Need at least {min_train_rows}."
        )

    X_train_c = sm.add_constant(X_train, has_constant="add")
    model = sm.OLS(y_train, X_train_c).fit()

    X_last_c = sm.add_constant(X_last, has_constant="add")
    pred = model.get_prediction(X_last_c)
    frame = pred.summary_frame(alpha=alpha)

    mean = float(frame["mean"].iloc[0])
    lower_r = float(frame["obs_ci_lower"].iloc[0])
    upper_r = float(frame["obs_ci_upper"].iloc[0])

    pred_close = last_close * float(np.exp(mean))
    lower_close = last_close * float(np.exp(lower_r))
    upper_close = last_close * float(np.exp(upper_r))

    return ForecastResult(
        as_of_date=as_of_date,
        last_close=last_close,
        pred_return=mean,
        lower_return=lower_r,
        upper_return=upper_r,
        pred_close=pred_close,
        lower_close=lower_close,
        upper_close=upper_close,
        n_train=len(X_train),
        model_r2=float(model.rsquared) if model.rsquared is not None else None,
    )
