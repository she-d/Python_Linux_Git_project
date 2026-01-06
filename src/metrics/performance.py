import numpy as np
import pandas as pd


def infer_periods_per_year(df: pd.DataFrame) -> float:
    """
    Infer periods/year from timestamp frequency.
    Works for intraday 5m and also for daily data.
    """
    if "timestamp" not in df.columns or len(df) < 3:
        # fallback: daily
        return 252.0

    ts = pd.to_datetime(df["timestamp"], utc=True).sort_values()
    delta = (ts.iloc[-1] - ts.iloc[0]).total_seconds()
    if delta <= 0:
        return 252.0

    # average step in seconds
    steps = ts.diff().dropna().dt.total_seconds()
    step = float(steps.median()) if len(steps) else 24 * 3600.0

    if step <= 0:
        return 252.0

    # trading minutes per day ~ 390 (US equities). We'll use 252 trading days/year.
    periods_per_day = (390 * 60) / step  # 390 minutes in seconds / step
    return float(252.0 * periods_per_day)


def total_return(equity: pd.Series) -> float:
    if equity is None or len(equity) < 2:
        return 0.0
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def annualized_vol(returns: pd.Series, periods_per_year: float) -> float:
    r = returns.dropna()
    if len(r) < 2:
        return 0.0
    return float(r.std(ddof=0) * np.sqrt(periods_per_year))


def sharpe_ratio(returns: pd.Series, periods_per_year: float, risk_free_rate: float = 0.0) -> float:
    """
    returns: periodic returns
    risk_free_rate: annual risk-free rate (default 0)
    """
    r = returns.dropna()
    if len(r) < 2:
        return 0.0

    rf_per_period = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0
    excess = r - rf_per_period

    vol = excess.std(ddof=0)
    if vol == 0:
        return 0.0

    return float(excess.mean() / vol * np.sqrt(periods_per_year))


def max_drawdown(equity: pd.Series) -> float:
    """
    Returns max drawdown as a negative number (e.g., -0.25 for -25%)
    """
    if equity is None or len(equity) < 2:
        return 0.0
    eq = equity.astype(float)
    running_max = eq.cummax()
    dd = eq / running_max - 1.0
    return float(dd.min())


def compute_metrics(df: pd.DataFrame, equity_col: str, ret_col: str) -> dict:
    ppy = infer_periods_per_year(df)
    eq = df[equity_col]
    r = df[ret_col]

    return {
        "total_return": total_return(eq),
        "volatility": annualized_vol(r, ppy),
        "sharpe": sharpe_ratio(r, ppy, risk_free_rate=0.0),
        "max_drawdown": max_drawdown(eq),
        "periods_per_year": ppy,
    }
