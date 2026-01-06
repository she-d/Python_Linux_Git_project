import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data.yahoo import get_candles_yahoo
from src.strategies.buy_hold import buy_and_hold
from src.metrics.performance import compute_metrics


def main():
    asset = "AAPL"
    interval = "5m"
    period = "5d"

    prices = get_candles_yahoo(asset, interval=interval, period=period)
    out = buy_and_hold(prices, initial_value=100.0)

    metrics = compute_metrics(out, equity_col="equity_bh", ret_col="ret")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("report") / "daily"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}_{asset}.md"

    last_close = float(out["close"].iloc[-1])
    first_close = float(out["close"].iloc[0])

    md = []
    md.append(f"# Daily Report — {asset}")
    md.append(f"- Date (UTC): **{today}**")
    md.append("")
    md.append("## Latest data")
    md.append(f"- First close: **{first_close:.2f}**")
    md.append(f"- Last close: **{last_close:.2f}**")
    md.append("")
    md.append("## Buy & Hold metrics (annualized where applicable)")
    md.append(f"- Total return: **{metrics['total_return']*100:.2f}%**")
    md.append(f"- Volatility: **{metrics['volatility']*100:.2f}%**")
    md.append(f"- Sharpe: **{metrics['sharpe']:.2f}**")
    md.append(f"- Max drawdown: **{metrics['max_drawdown']*100:.2f}%**")
    md.append("")
    md.append(f"_Data source: Yahoo intraday ({interval}, {period})._")

    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote report: {out_path.resolve()}")


if __name__ == "__main__":
    main()
