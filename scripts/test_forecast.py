from pathlib import Path
import sys

import pandas as pd

# Allow "from src..." imports when running as a script
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.models.linear_forecast import forecast_next_day_ols_from_daily  # noqa: E402

def main():
    csv_path = ROOT / "data" / "aapl_daily.csv"
    if not csv_path.exists():

        raise FileNotFoundError(
        f"CSV not found at {csv_path}. "
        f"Run: python scripts/fetch_daily_yahoo.py"
    )

    df = pd.read_csv(csv_path)

    res = forecast_next_day_ols_from_daily(
     df_daily=df,
        date_col="date",
        close_col="close",
        lags=5,
        vol_window=10,
        momentum_lookback=10,
        alpha=0.05,      # 95% prediction interval
        min_train_rows=60,
    )

    print("=== OLS Daily Forecast (next day) ===")
    print(f"As of date   : {res.as_of_date}")
    print(f"Last close   : {res.last_close:.4f}")
    print(f"Pred close   : {res.pred_close:.4f}")
    print(f"PI 95% close : [{res.lower_close:.4f}, {res.upper_close:.4f}]")
    print(f"Pred return  : {res.pred_return:.6f}")
    print(f"PI 95% return: [{res.lower_return:.6f}, {res.upper_return:.6f}]")
    print(f"Train rows   : {res.n_train}")
    if res.model_r2 is not None:
        print(f"R^2 (train)  : {res.model_r2:.4f}")


if __name__ == "__main__":
    main()
