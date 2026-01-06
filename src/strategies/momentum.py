import pandas as pd


def momentum_strategy(
    prices: pd.DataFrame,
    lookback: int = 20,
    initial_value: float = 100.0,
) -> pd.DataFrame:
    """
    Simple momentum strategy (long/flat):
    - signal = 1 if past return over `lookback` periods > 0 else 0
    - strategy return = signal(t-1) * asset_return(t)

    Expected columns: timestamp, close
    Output columns: ret, signal, strat_ret, equity_mom
    """
    df = prices.copy().sort_values("timestamp").reset_index(drop=True)

    df["ret"] = df["close"].pct_change().fillna(0.0)

    # past return over lookback periods
    df["mom"] = df["close"].pct_change(lookback)

    # long/flat signal
    df["signal"] = (df["mom"] > 0).astype(int)

    # trade next bar (avoid look-ahead bias)
    df["signal_lag"] = df["signal"].shift(1).fillna(0).astype(int)

    df["strat_ret"] = df["signal_lag"] * df["ret"]
    df["equity_mom"] = initial_value * (1.0 + df["strat_ret"]).cumprod()

    return df
