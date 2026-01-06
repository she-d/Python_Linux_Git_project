import pandas as pd
import yfinance as yf


def get_candles_yahoo(symbol: str = "AAPL", interval: str = "5m", period: str = "5d") -> pd.DataFrame:
    df = yf.download(symbol, interval=interval, period=period, progress=False)

    if df is None or df.empty:
        raise RuntimeError("Yahoo Finance returned empty dataframe.")

    # If columns are MultiIndex (common with yfinance), reduce to single level
    if isinstance(df.columns, pd.MultiIndex):
        # If second level contains tickers, select the requested symbol
        if symbol in df.columns.get_level_values(-1):
            df = df.xs(symbol, axis=1, level=-1)
        # If it's still MultiIndex (sometimes), just keep first level names
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    ts_col = "Datetime" if "Datetime" in df.columns else "Date"

    out = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(df[ts_col], utc=True),
            "asset": symbol,
            "open": pd.Series(df["Open"]).astype(float),
            "high": pd.Series(df["High"]).astype(float),
            "low": pd.Series(df["Low"]).astype(float),
            "close": pd.Series(df["Close"]).astype(float),
            "volume": pd.Series(df["Volume"]).astype(float) if "Volume" in df.columns else 0.0,
        }
    )

    out = out.drop_duplicates(subset=["timestamp", "asset"]).sort_values("timestamp").reset_index(drop=True)
    return out
