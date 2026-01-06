import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# --- SETUP PATH ---
# Move up 1 level (scripts/ -> root) to find 'src' directory
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Import custom modules from src
from src.data.yahoo import get_candles_yahoo
from src.strategies.portfolio_allocation import compute_portfolio_equity
from src.metrics.risk_analysis import compute_risk_metrics

def generate_daily_report():
    """
    Generates a daily text report with portfolio metrics.
    Intended to be run via CRON or task scheduler.
    """
    print("--- Starting Daily Portfolio Report (Quant B) ---")
    
    # Fixed Configuration for the report
    assets = ["AAPL", "MSFT", "KO"]
    weights = {"AAPL": 0.33, "MSFT": 0.33, "KO": 0.34}
    
    # Data Retrieval
    print("Fetching data...")
    prices = {}
    for asset in assets:
        try:
            # Fetch 3 months of data to ensure enough points for volatility calculation
            df = get_candles_yahoo(asset, period="3mo", interval="1d")
            if not df.empty:
                prices[asset] = df.set_index("timestamp")["close"]
        except Exception as e:
            print(f"Error fetching {asset}: {e}")

    if not prices:
        print("No data retrieved. Aborting.")
        return

    df_prices = pd.DataFrame(prices).dropna()
    
    # Calculations (Strategy & Risk)
    port_res = compute_portfolio_equity(df_prices, weights)
    corr, vol_metrics = compute_risk_metrics(df_prices, weights)
    
    # Extract latest values for the report
    current_val = port_res["equity_curve"].iloc[-1]
    daily_return = port_res["port_ret"].iloc[-1]
    portfolio_vol = vol_metrics.loc["PORTFOLIO", "Volatility"]

    # Write report to file
    today = datetime.now().strftime("%Y-%m-%d")
    # Save report to project root for easy access
    report_filename = ROOT / f"portfolio_report_{today}.txt"
    
    with open(report_filename, "w") as f:
        f.write(f"=== DAILY PORTFOLIO REPORT : {today} ===\n\n")
        f.write(f"Total Portfolio Value (Base 100): {current_val:.2f}\n")
        f.write(f"Daily Return: {daily_return:.2%}\n")
        f.write(f"Annualized Volatility: {portfolio_vol:.2%}\n")
        f.write("\n--- Asset Allocation ---\n")
        for a, w in weights.items():
            f.write(f" - {a}: {w*100}%\n")
    
    print(f"Report saved to: {report_filename}")

if __name__ == "__main__":
    generate_daily_report()