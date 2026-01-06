import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data.finnhub import get_quote
from src.data.yahoo import get_candles_yahoo
from src.data.storage import upsert_csv


def main():
    q = get_quote("AAPL")
    print("QUOTE AAPL (Finnhub):", q)

    df = get_candles_yahoo("AAPL", interval="5m", period="5d")
    print("\nCANDLES (Yahoo) HEAD:")
    print(df.head())

    print("\nCANDLES (Yahoo) TAIL:")
    print(df.tail())

    saved = upsert_csv(df, "data/aapl_5min.csv")
    print(f"\nSaved rows: {len(saved)}")
    print("Saved file:", Path("data/aapl_5min.csv").resolve())


if __name__ == "__main__":
    main()
