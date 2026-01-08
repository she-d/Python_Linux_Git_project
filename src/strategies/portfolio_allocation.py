import pandas as pd
import numpy as np
from typing import Dict

def compute_portfolio_equity(prices_df: pd.DataFrame, weights: Dict[str, float], initial_value: float = 100.0) -> pd.DataFrame:
    
    returns = prices_df.pct_change().dropna()
    
    w_vector = np.array([weights[asset] for asset in prices_df.columns])
    
    #weight normalization
    if np.sum(w_vector) != 0:
        w_vector = w_vector / np.sum(w_vector)
    
    #global yield calculation
    portfolio_returns = returns.dot(w_vector)
    
    #Equity Curve base 100
    equity_curve = (1 + portfolio_returns).cumprod() * initial_value
    
    #final result
    output = pd.DataFrame({
        "port_ret": portfolio_returns,
        "equity_curve": equity_curve
    }, index=returns.index)
    
    return output