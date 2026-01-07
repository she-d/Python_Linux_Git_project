from pathlib import Path
import yfinance as yf
import pandas as pd


def main():
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    symbol = "AAPL"
    out_path = data_dir / "aapl_daily.csv"

    # 2 years gives enough daily points for OLS intervals
    df = yf.download(
        symbol,
        period="2y",
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    if df is None or df.empty:
        raise RuntimeError("Yahoo download returned empty data.")

    df = df.reset_index()

    # yfinance typically returns columns: Date, Open, High, Low, Close, Adj Close, Volume
    # Normalize columns 
    if "Date" in df.columns:
        df.rename(columns={"Date": "date"}, inplace=True)
    if "Close" in df.columns:
        df.rename(columns={"Close": "close"}, inplace=True)

    keep = ["date", "close"]
    df = df[keep].dropna()
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)

    df.to_csv(out_path, index=False)
    print(f"Wrote daily data: {out_path} (rows={len(df)})")


if __name__ == "__main__":
    main()
