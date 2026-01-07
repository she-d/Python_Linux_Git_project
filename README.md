# Python_Linux_Git_project : Quant Finance Dashboard
Real-time financial dashboard for asset and portfolio analysis.
Built with **Python + Streamlit**, deployed on an **AWS Ubuntu VM** with **cron** for daily reporting and **systemd** for 24/7 uptime.

## Teacher Quickstart 
### Option A — Run locally (recommended for quick testing)
1) Create a virtual environment
```bash
python -m venv .venv
On Windows PowerShell:
.venv\Scripts\Activate.ps1
On macOS/Linux:
source .venv/bin/activate
2) Install dependencies 
pip install -r requirements.txt
3) Set Finnhub API key (for live quote)
On Windows PowerShell:
$env:FINNHUB_API_KEY="YOUR_KEY_HERE"
On macOS/Linux:
export FINNHUB_API_KEY="YOUR_KEY_HERE"
4) Run the dashboard 
streamlit run app/streamlit_app.py

### Option B — Run on the AWS VM (deployed 24/7)
sudo systemctl status streamlit-quant --no-pager
sudo systemctl restart streamlit-quant
view the lofs:
journalctl -u streamlit-quant -n 80 --no-pager
Acess the app:
ssh -i "C:\path\to\quant-key.pem" -L 8501:localhost:8501 ubuntu@<PUBLIC_IP>

###Project goal
Build and deploy an online platform that:
- retrieves financial data from a dynamic source in near real-time
- displays it on an interactive dashboard
- implements quantitative strategies and backtesting tools
- computes and displays key performance metrics
- refreshes automatically every few minutes
- generates a daily report via Linux (cron)
- runs 24/7 on a hosted Linux machine (systemd)

##Data source 
We retrieve intraday stock prices for Apple (AAPL) using: 
- **Finnhub API**: real-time quote (current price)
- **Yahoo Finance (via `yfinance`)**: intraday candles (5m / 15m / 30m / 60m)

> Note: We initially tried Finnhub intraday candles but encountered access limitations (403), so the app uses Yahoo candles as a reliable intraday source.

##Team & division of work 
### Quant A — Sherynne (Single Asset Analysis) 
- Asset: **AAPL**
- Data: intraday candles (Yahoo) + live quote (Finnhub)
- Strategies: **Buy & Hold**, **Momentum**
- Metrics: Total return, Volatility, Max Drawdown, Sharpe ratio
- Streamlit dashboard with interactive controls + main chart (price + strategy equity curve)
- Daily report via cron (20:00 Paris)
- 24/7 deployment via systemd on AWS Ubuntu
- Bonus: Forecast page (OLS regression + prediction intervals)

### Quant B — Raphaël (Portfolio Analysis)
- Assets: **AAPL**, **MSFT**, **KO**
- Scope: **Multi-Asset Portfolio Management**
- Strategies: **Portfolio Allocation** (User-defined weights vs Equal Weights)
- Metrics: Correlation Matrix, Portfolio Volatility, VaR (Value at Risk)
- Dedicated Streamlit Dashboard 
- Automated Daily Reporting via Cron (Text report generation)
- Unit Testing for logic validation

## Data Contract (Columns)

Minimum required columns (shared format):

| column     | type                     | description |
|-----------|---------------------------|-------------|
| timestamp | datetime (UTC)            | candle timestamp |
| asset     | str                       | ticker symbol (e.g. `"AAPL"`) |
| close     | float                     | closing price |


## Strategies (Quant A)
###1) Buy & Hold
Benchmark strategy: always invested in the asset

###2) Momentum 
- Parameter: `lookback` (e.g., 20 periods)
- Signal (long/flat):  
  - `1` if past return over lookback > 0  
  - `0` otherwise  
- Signal is lagged to avoid look-ahead bias

## Strategies (Quant B)
### Portfolio Allocation
Unlike single-asset strategies, this module manages a basket of assets to optimize risk/reward.
- Logic: Reconstructs the equity curve based on weighted returns of selected assets (`AAPL`, `MSFT`, `KO`...).
- Weighting Schemes:
  - Equal Weighted: Automatically assigns $1/N$ weight to each asset (default).
  - Custom Weighted: User can manually adjust exposure via the sidebar sliders.
- Rebalancing: Implicitly assumes daily rebalancing to maintain target weights in the simulation.

## Metrics (Quant A)
Displayed on the dashboard:
-Total return
-Volatility (annualized)
-Max Drawdown 
-Sharpe ratio (annualized, risk-free rate =0 by default)

Note : Annualization factor depends on the data frequency (default: 5-minute intraday candles)

## Metrics (Quant B)
Focused on diversification and risk management:
-Correlation Matrix
-Portfolio Volatility: Annualized standard deviation of the weighted portfolio.
-Value at Risk (VaR 95%)
-Portfolio Sharpe Ratio.

## Auto-refresh (Every 5 Minutes)

The Streamlit dashboard refreshes automatically every **5 minutes**.

- Uses `streamlit-autorefresh`
- Data fetches are cached with `@st.cache_data(ttl=300)` to avoid excessive API calls

## Bonus — Forecast (Baseline OLS + Prediction Intervals)
OLS regression next-day forecast
Prediction intervals (90/95/99%)
Streamlit page: app/pages/2_Forecast.py
Daily history for forecast is fetched via: scripts/fetch_daily_yahoo.py → saves data/aapl_daily.csv

## Daily Report (Linux cron)
A daily report is generated at a fixed time (**20:00 Paris**) and stored locally on the VM.

## Timezone(VM)
sudo timedatectl set-timezone Europe/Paris

## Cron entry (VM)
0 20 * * * cd /home/ubuntu/Python_Linux_Git_project && /home/ubuntu/Python_Linux_Git_project/.venv/bin/python scripts/generate_daily_report.py >> report/daily/cron.log 2>&1

## 24/7 Deployment (systemd)
Streamlit runs as a systemd service (streamlit-quant) with auto-restart and reboot persistence.
Status : sudo systemctl status streamlit-quant --no-pager
Restart: sudo systemctl status streamlit-quant --no-pager
Logs: journalctl -u streamlit-quant -n 80 --no-pager

##Repository structure 
app/                      # Streamlit app (Quant A)
  streamlit_app.py
  app_quant_b.py          # Quant B Dashboard
  pages/
    2_Forecast.py         # bonus forecast page
src/
  data/                   # data retrieval
    finnhub.py
    yahoo.py
  strategies/             # backtesting strategies
    buy_hold.py
    momentum.py
    portfolio_allocation.py
  metrics/                # performance metrics
    performance.py
    risk_analysis.py
  models/                 # forecasting models
    linear_forecast.py
scripts/
  generate_daily_report.py
  generate_portfolio_report.py
  fetch_daily_yahoo.py
  test_forecast.py
  test_portfolio.py
report/
  daily/                  # daily reports + cron logs
.streamlit/
  config.toml             # theme (pro User Interface(UI))
  style.css               # CSS polish (pro UI)
requirements.txt

### Environment variables 
Set your Finnhub API key:
On Windows PowerShell: $env:FINNHUB_API_KEY="YOUR_KEY_HERE"


