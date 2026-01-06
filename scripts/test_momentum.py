import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data.yahoo import get_candles_yahoo
from src.strategies.momentum import momentum_strategy


def main():
    prices = get_candles_yahoo("AAPL", interval="5m", period="5d")

    out = momentum_strategy(prices, lookback=20, initial_value=100.0)

    print(out[["timestamp", "close", "ret", "signal", "strat_ret", "equity_mom"]].head(30))
    print(out[["timestamp", "close", "ret", "signal", "strat_ret", "equity_mom"]].tail())

    total_return = out["equity_mom"].iloc[-1] / out["equity_mom"].iloc[0] - 1
    print("\nTotal return (Momentum):", total_return)


if __name__ == "__main__":
    main()
