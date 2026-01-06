import pandas as pd
import numpy as np
from typing import Dict, Tuple

def compute_risk_metrics(prices_df: pd.DataFrame, weights: Dict[str, float]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    
    #calculate daily returns for all assets
    returns = prices_df.pct_change().dropna()

    #compute the correlation matrix (Required by Quant B specs)
    corr_matrix = returns.corr()

    #align weights vector with the DataFrame columns
    w_vector = np.array([weights[asset] for asset in prices_df.columns])
    
    #normalize weights to ensure sum is 1
    if np.sum(w_vector) != 0:
        w_vector = w_vector / np.sum(w_vector)

    #calculate annualized volatility for each individual asset (Standard Deviation * sqrt(252))
    asset_vols = returns.std() * np.sqrt(252)

    #calculate the annualized covariance matrix
    cov_matrix = returns.cov() * 252

    #calculate portfolio volatility using matrix algebra: sqrt(w.T * Cov * w)
    port_vol = np.sqrt(np.dot(w_vector.T, np.dot(cov_matrix, w_vector)))

    #create a summary DataFrame comparing assets and portfolio
    vol_data = {
        "Asset": list(prices_df.columns) + ["PORTFOLIO"],
        "Volatility": list(asset_vols) + [port_vol]
    }
    
    vol_metrics = pd.DataFrame(vol_data).set_index("Asset")

    return corr_matrix, vol_metrics