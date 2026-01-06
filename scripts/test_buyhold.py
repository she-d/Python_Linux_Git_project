import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data.yahoo import get_candles_yahoo
from src.strategies.buy_hold import buy_and_hold


def main():
    prices = get_candles_yahoo("AAPL", interval="5m", period="5d")
    out = buy_and_hold(prices, initial_value=100.0)

    print(out[["timestamp", "close", "ret", "equity_bh"]].head())
    print(out[["timestamp", "close", "ret", "equity_bh"]].tail())

    total_return = out["equity_bh"].iloc[-1] / out["equity_bh"].iloc[0] - 1
    print("\nTotal return (Buy & Hold):", total_return)


if __name__ == "__main__":
    main()
