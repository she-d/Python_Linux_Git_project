# Python_Linux_Git_project : Quant Finance Dashboard
Real-time financial dashboard for asset and portfolio analysis.

###Project goal
Build and deploy an online platform that:
-retrieves financial data from a dynamic source in near real-time
-displays it on an interactive dashboard
-implements quantitative strategies and backtesting tools
-computes and displays key performance metrics
-generates a daily report via linux

##Data source 
We retrieve intraday stock prices for Apple (AAPL) using Finnhub AP

##Team & division of work 
**Quant A : Sherynne : Single Asset Analysis
-Asset : AAPL (intraday 5-min candles via Finnhub)
-Strategies: Buy & Hold, Momentum
-Metrics: Total return, Volatility, Max Drawdown, Sharpe ratio
-Streamlit dashboard with interactive controls and main chart (price + strategy equity curve)

**Quant B: Raphaël : Portfolio Analysis
-Portfolio simulation and portfolio-level analytics
...

##Columns required
| column      | type   | description |
|------------|--------|-------------|
| timestamp  | datetime (UTC) or int | candle timestamp (UTC) |
| asset      | str    | ticker symbol ("AAPL") |
| close      | float  | closing price |

(optional on verra) `open`, `high`, `low`, `volume`

##Strategies
###1) Buy & Hold
Benchmark strategy: always invested in the asset

###2) Momentum 
-parameter: 'lookback' (exple 20periods)
-signal:
-long/flat : 1 if past return over lookback >0 else 0

##Metrics
Displayed on the dashboard:
-Total return
-Volatility (annualized)
-Max Drawdown 
-Sharpe ratio (annualized, risk-free rate =0 by default)

Note : Annualization factor depends on the data frequency (default: 5-minute intraday candles)

##Daily report (Linux cron)
A daily report is generated at a fixed time (default: 20:00) and stored locally on the VM.

Output Location:
-'report/daily/YYY-MM-DD_AAPL.md' (or '.csv')

The repository contains:
-a script in 'scripts/' to generate the report
-an example cron configuration in 'scripts/cron/'
-documentation below explaining how to install/enable the cron job

##Repository structure 
app/ #Streamlit app
src/
data/ #data retrieval + cleaning + storgae
strategies/ #backtesting strategies (buy&hold, momentum)
metrics/ #performance metrics
scripts/ #cron scripts (daily report, optional fetchers)
report/ #generated reports (daily)

### 1) Environment variables 
Set your Finnhub API key:
bash
export FINNHUB_API_KEY="YOUR_KEY_HERE"
