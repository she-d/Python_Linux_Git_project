import pandas as pd


def buy_and_hold(prices: pd.DataFrame, initial_value: float = 100.0) -> pd.DataFrame:
    """
    Buy & Hold equity curve from close prices.
    Expected columns: timestamp, close
    Output columns: ret, equity_bh
    """
    df = prices.copy().sort_values("timestamp").reset_index(drop=True)
    df["ret"] = df["close"].pct_change().fillna(0.0)
    df["equity_bh"] = initial_value * (1.0 + df["ret"]).cumprod()
    return df
