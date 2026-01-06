import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data.yahoo import get_candles_yahoo
from src.strategies.buy_hold import buy_and_hold
from src.strategies.momentum import momentum_strategy
from src.metrics.performance import compute_metrics


def main():
    prices = get_candles_yahoo("AAPL", interval="5m", period="5d")

    bh = buy_and_hold(prices, initial_value=100.0)
    bh_metrics = compute_metrics(bh, equity_col="equity_bh", ret_col="ret")

    mom = momentum_strategy(prices, lookback=20, initial_value=100.0)
    mom_metrics = compute_metrics(mom, equity_col="equity_mom", ret_col="strat_ret")

    print("\nBUY & HOLD METRICS")
    print(bh_metrics)

    print("\nMOMENTUM METRICS")
    print(mom_metrics)


if __name__ == "__main__":
    main()
