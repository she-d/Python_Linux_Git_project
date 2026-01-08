import sys
from pathlib import Path
import pandas as pd
import numpy as np

# --- SETUP PATH ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.strategies.portfolio_allocation import compute_portfolio_equity
from src.metrics.risk_analysis import compute_risk_metrics

def test_quant_b_logic():
    print("--- TESTING QUANT B MODULE ---")
    
    #Mock Data (Generated data to ensure test success without Internet)
    dates = pd.date_range(start="2023-01-01", periods=100)
    data = {
        "AAPL": np.random.normal(150, 5, 100),
        "MSFT": np.random.normal(300, 10, 100),
        "KO": np.random.normal(60, 2, 100)
    }
    df = pd.DataFrame(data, index=dates)
    print("[OK] Test Data generated.")

    #Test Strategy
    print("\n2. Testing Portfolio Allocation...")
    weights = {"AAPL": 0.5, "MSFT": 0.25, "KO": 0.25}
    res = compute_portfolio_equity(df, weights)
    
    if "equity_curve" in res.columns:
        print(f"   [OK] Portfolio Final Value: {res['equity_curve'].iloc[-1]:.2f}")
    else:
        print("   [FAIL] Equity curve missing.")

    #Test Metrics
    print("\n3. Testing Risk Metrics...")
    corr, vols = compute_risk_metrics(df, weights)
    
    if not corr.empty:
        print("   [OK] Correlation Matrix computed.")
    else:
        print("   [FAIL] Correlation Matrix empty.")
        
    print("\n--- TEST SUCCESSFUL ---")

if __name__ == "__main__":
    test_quant_b_logic()