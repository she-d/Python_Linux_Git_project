
import os
import time
import requests
import pandas as pd


BASE_URL = "https://finnhub.io/api/v1"


def _api_key() -> str:
    key = os.getenv("FINNHUB_API_KEY")
    if not key:
        raise RuntimeError(
            "FINNHUB_API_KEY is missing. "
            "PowerShell: $env:FINNHUB_API_KEY='YOUR_KEY' | Linux/macOS: export FINNHUB_API_KEY='YOUR_KEY'"
        )
    return key


def get_quote(symbol: str = "AAPL") -> dict:
    r = requests.get(
        f"{BASE_URL}/quote",
        params={"symbol": symbol, "token": _api_key()},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def get_candles(symbol: str = "AAPL", resolution: str = "5", lookback_days: int = 5) -> pd.DataFrame:
    now = int(time.time())
    frm = now - lookback_days * 24 * 60 * 60

    r = requests.get(
        f"{BASE_URL}/stock/candle",
        params={
            "symbol": symbol,
            "resolution": resolution,
            "from": frm,
            "to": now,
            "token": _api_key(),
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()

    if data.get("s") != "ok":
        raise RuntimeError(f"Finnhub candle API returned s={data.get('s')} payload={data}")

    df = pd.DataFrame(
        {"timestamp": pd.to_datetime(data["t"], unit="s", utc=True),
            "close": data["c"],
            "open": data["o"],
            "high": data["h"],
            "low": data["l"],
            "volume": data["v"],
        })
    
    df["asset"] = symbol

    df = df[["timestamp", "asset", "close", "open", "high", "low", "volume"]]
    df = df.drop_duplicates(subset=["timestamp", "asset"]).sort_values("timestamp").reset_index(drop=True)
    return df
    
